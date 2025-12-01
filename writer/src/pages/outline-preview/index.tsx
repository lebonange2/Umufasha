import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import OutlinePreview, { OutlineData } from '../../features/outline/OutlinePreview';
import { convertOutlineToDocument } from '../../features/outline/outlineConverter';
import { structureStorage } from '../../features/structure/storage';
import { LLMAdapter } from '../../lib/llmAdapter';
import { buildSystemPrompt, buildUserPrompt } from '../../features/writer/promptBuilders';
import { WriterMode } from '../../lib/types';

export default function OutlinePreviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [outline, setOutline] = useState<OutlineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [generationProgress, setGenerationProgress] = useState('');
  const llmAdapter = useRef(new LLMAdapter());

  const generateOutline = useCallback(async () => {
    setIsGenerating(true);
    setGenerationProgress('Preparing outline generation...');

    try {
      // Get context from localStorage
      const contextData = localStorage.getItem('outline_generation_context');
      if (!contextData) {
        throw new Error('No context found for outline generation');
      }

      const { content, settings, selectedDocuments, textContext } = JSON.parse(contextData);

      const systemPrompt = buildSystemPrompt('outline', settings);
      const userPrompt = buildUserPrompt('outline', '', content, undefined);

      const request = {
        system: systemPrompt,
        prompt: userPrompt,
        context: content,
        document_context: selectedDocuments?.length > 0 ? selectedDocuments : undefined,
        text_context: textContext?.trim() || undefined,
        mode: 'outline' as WriterMode,
        provider: settings.provider,
        model: settings.model,
        params: {
          temperature: settings.temperature,
          max_tokens: settings.maxTokens || 2000,
        },
        stream: true,
      };

      let accumulatedText = '';
      setGenerationProgress('Generating outline...');

      for await (const chunk of llmAdapter.current.stream(request)) {
        if (chunk.error) {
          console.error('LLM Error:', chunk.error);
          alert(`AI Error: ${chunk.error}`);
          setIsGenerating(false);
          return;
        }

        if (chunk.done) break;

        accumulatedText += chunk.token;
        setGenerationProgress(`Generating outline... (${accumulatedText.length} characters)`);
      }
      
      // Log the full response for debugging
      console.log('Full AI response:', accumulatedText);
      console.log('Response length:', accumulatedText.length);

      // Parse the generated outline
      try {
        let outlineJson = accumulatedText.trim();
        
        // Try to extract JSON from the response
        // Remove markdown code blocks if present
        outlineJson = outlineJson.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
        
        // Try to find JSON object in the text (in case there's extra text)
        const jsonMatch = outlineJson.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          outlineJson = jsonMatch[0];
        }
        
        // Try to parse
        let parsedOutline: OutlineData;
        try {
          parsedOutline = JSON.parse(outlineJson);
        } catch (parseError) {
          // If direct parse fails, try to fix common issues
          console.warn('Initial parse failed, attempting to fix JSON:', parseError);
          
          // Fix common JSON issues
          let fixedJson = outlineJson;
          
          // 1. Fix missing commas between array elements (e.g., "text1" "text2" -> "text1", "text2")
          fixedJson = fixedJson.replace(/"\s+"(?=\s*[\]}])/g, '", "');
          fixedJson = fixedJson.replace(/"\s+"(?=\s*[,\]])/g, '", "');
          
          // 2. Fix missing commas between object properties
          fixedJson = fixedJson.replace(/}\s*{/g, '}, {');
          fixedJson = fixedJson.replace(/]\s*\[/g, '], [');
          
          // 3. Fix missing commas after closing quotes before opening quotes
          fixedJson = fixedJson.replace(/"\s*"(?=\s*[,\]:])/g, '", "');
          
          // 4. Fix missing commas in beats arrays (common issue)
          fixedJson = fixedJson.replace(/"beats":\s*\[([^\]]*)"([^"]+)"\s*"([^"]+)"([^\]]*)\]/g, (match, before, text1, text2, after) => {
            // Check if there's a missing comma between two strings
            if (!before.includes(',') && !after.includes(',')) {
              return `"beats": [${before}"${text1}", "${text2}"${after}]`;
            }
            return match;
          });
          
          // 5. Remove trailing commas
          fixedJson = fixedJson.replace(/,(\s*[}\]])/g, '$1');
          
          // 6. Try to find and extract the largest valid JSON object
          let bestJson = fixedJson;
          let bestError: any = null;
          
          // Try progressively shorter versions from the end
          for (let i = fixedJson.length; i > 100; i -= 10) {
            const truncated = fixedJson.substring(0, i);
            // Try to find the last complete object
            const lastBrace = truncated.lastIndexOf('}');
            if (lastBrace > 0) {
              const candidate = truncated.substring(0, lastBrace + 1);
              try {
                JSON.parse(candidate); // Test if valid
                bestJson = candidate;
                break;
              } catch (e) {
                if (!bestError) bestError = e;
              }
            }
          }
          
          try {
            parsedOutline = JSON.parse(bestJson);
          } catch (secondError) {
            // Last attempt: try to fix missing commas more aggressively
            let aggressiveFix = bestJson;
            
            // Fix pattern: "text1" "text2" -> "text1", "text2"
            aggressiveFix = aggressiveFix.replace(/"([^"]+)"\s+"([^"]+)"/g, (match, text1, text2) => {
              // Only fix if it's inside an array (check context)
              const before = aggressiveFix.substring(0, aggressiveFix.indexOf(match));
              const afterBracket = before.lastIndexOf('[');
              const afterBrace = before.lastIndexOf('{');
              if (afterBracket > afterBrace) {
                return `"${text1}", "${text2}"`;
              }
              return match;
            });
            
            try {
              parsedOutline = JSON.parse(aggressiveFix);
            } catch (finalError) {
              // Show the actual error and generated text for debugging
              console.error('Failed to parse outline JSON after all fixes:', finalError);
              console.error('Original text:', accumulatedText);
              console.error('Attempted fixes:', {
                initial: outlineJson.substring(0, 200),
                fixed: bestJson.substring(0, 200),
                aggressive: aggressiveFix.substring(0, 200),
              });
              
              // Try one more time with a more aggressive cleanup - find the first complete JSON object
              const firstBrace = aggressiveFix.indexOf('{');
              if (firstBrace !== -1) {
                // Find the matching closing brace
                let braceCount = 0;
                let lastBrace = -1;
                for (let i = firstBrace; i < aggressiveFix.length; i++) {
                  if (aggressiveFix[i] === '{') braceCount++;
                  if (aggressiveFix[i] === '}') {
                    braceCount--;
                    if (braceCount === 0) {
                      lastBrace = i;
                      break;
                    }
                  }
                }
                
                if (lastBrace > firstBrace) {
                  const extracted = aggressiveFix.substring(firstBrace, lastBrace + 1);
                  // Fix missing commas one more time
                  const finalFix = extracted.replace(/"([^"]+)"\s+"([^"]+)"/g, '"$1", "$2"');
                  try {
                    parsedOutline = JSON.parse(finalFix);
                  } catch (lastError) {
                    throw new Error(`Failed to parse JSON. The AI may have returned invalid JSON. Error: ${lastError}. Generated text preview: ${accumulatedText.substring(0, 500)}...`);
                  }
                } else {
                  throw new Error(`No complete JSON object found in response. Generated text preview: ${accumulatedText.substring(0, 500)}...`);
                }
              } else {
                throw new Error(`No JSON object found in response. Generated text preview: ${accumulatedText.substring(0, 500)}...`);
              }
            }
          }
        }
        
        // Validate parsed outline
        if (!parsedOutline || typeof parsedOutline !== 'object') {
          throw new Error('Parsed outline is not a valid object');
        }
        
        // Ensure chapters array exists
        if (!parsedOutline.chapters || !Array.isArray(parsedOutline.chapters)) {
          console.warn('Outline missing chapters array, creating empty structure');
          parsedOutline.chapters = [];
        }
        
        // Handle the format where title is at root: { "title": "Africa", "chapters": [...] }
        const finalOutline: OutlineData = {
          title: parsedOutline.title || 'Untitled Document',
          chapters: parsedOutline.chapters || [],
        };
        
        // Validate that we have at least some structure
        if (finalOutline.chapters.length === 0) {
          console.warn('Generated outline has no chapters. Full response:', accumulatedText);
          console.warn('Parsed outline object:', parsedOutline);
          // Show warning but still set the outline so user can see it's empty
          alert('Warning: The generated outline appears to be empty (no chapters). Please check the browser console for details. You may need to provide more context or try again.');
        }
        
        setOutline(finalOutline);
        
        // Save to localStorage
        localStorage.setItem('pending_outline', JSON.stringify(finalOutline));
        setGenerationProgress('');
      } catch (error: any) {
        console.error('Failed to parse outline:', error);
        console.error('Full generated text:', accumulatedText);
        
        // Show more helpful error message
        const errorMsg = error.message || 'Unknown error';
        alert(`Failed to parse generated outline.\n\nError: ${errorMsg}\n\nPlease check the browser console for details. You may need to adjust the AI prompt or try again.`);
        setGenerationProgress('');
        setIsGenerating(false);
      }
    } catch (error: any) {
      console.error('Outline generation error:', error);
      alert(`Error: ${error.message}`);
      setGenerationProgress('');
    } finally {
      setIsGenerating(false);
    }
  }, []);

  useEffect(() => {
    // Check if we should generate outline
    if (location.state?.generateOutline) {
      generateOutline();
      setLoading(false);
      return;
    }

    // Get outline from location state or localStorage
    const outlineFromState = location.state?.outline;
    const outlineFromStorage = localStorage.getItem('pending_outline');

    if (outlineFromState) {
      setOutline(outlineFromState);
      setLoading(false);
    } else if (outlineFromStorage) {
      try {
        const parsed = JSON.parse(outlineFromStorage);
        // Handle the format where title is at root: { "title": "Africa", "chapters": [...] }
        if (parsed.title && parsed.chapters) {
          setOutline(parsed);
        } else if (parsed.chapters) {
          setOutline({
            title: parsed.title || 'Untitled Document',
            chapters: parsed.chapters,
          });
        } else {
          // Might be just the object with title and chapters
          setOutline(parsed);
        }
        setLoading(false);
      } catch (error) {
        console.error('Failed to parse outline:', error);
        setLoading(false);
      }
    } else {
      // No outline found, redirect or show error
      setLoading(false);
    }
  }, [location, generateOutline]);

  const handleApprove = async (approvedOutline: OutlineData) => {
    console.log('handleApprove called with outline:', approvedOutline);
    console.log('Outline chapters:', approvedOutline.chapters?.length || 0);
    
    if (isApproving) {
      console.warn('Approval already in progress, ignoring duplicate click');
      return;
    }
    
    setIsApproving(true);
    const overallStart = performance.now();
    
    try {
      // Validate outline before converting
      if (!approvedOutline || !approvedOutline.chapters || approvedOutline.chapters.length === 0) {
        alert('Cannot approve an empty outline. Please generate an outline with at least one chapter first.');
        setIsApproving(false);
        return;
      }

      console.log('Step 1: Converting outline to document...');
      const conversionStart = performance.now();
      
      // Convert outline to document structure
      const documentState = convertOutlineToDocument(approvedOutline);
      const conversionTime = performance.now() - conversionStart;
      
      console.log(`Conversion completed in ${conversionTime.toFixed(2)}ms`);
      console.log('Converted document state:', documentState);
      console.log('Number of nodes:', Object.keys(documentState.nodes).length);
      console.log('Root ID:', documentState.rootId);

      // Generate draftId early
      const draftId = `draft_${Date.now()}`;
      
      // Save to storage with timeout (non-blocking)
      console.log('Step 2: Saving to storage...');
      const storageStart = performance.now();
      
      // Try to save, but don't block if it fails
      const savePromise = (async () => {
        try {
          // Add timeout for storage initialization
          const initPromise = structureStorage.init();
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Storage initialization timeout')), 3000)
          );
          await Promise.race([initPromise, timeoutPromise]);
          
          console.log('Saving draft with ID:', draftId);
          
          // Add timeout for save operation
          const savePromise = structureStorage.saveStructuredDraft(draftId, documentState);
          const saveTimeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Save operation timeout')), 3000)
          );
          await Promise.race([savePromise, saveTimeoutPromise]);
          
          const storageTime = performance.now() - storageStart;
          console.log(`Storage completed in ${storageTime.toFixed(2)}ms`);
          console.log('Saved to storage with draftId:', draftId);
        } catch (storageError: any) {
          console.warn('Storage operation failed or timed out:', storageError);
          // Save to localStorage as fallback
          try {
            localStorage.setItem(`writer_structure_${draftId}`, JSON.stringify({ id: draftId, state: documentState, updatedAt: Date.now() }));
            console.log('Saved to localStorage as fallback');
          } catch (e) {
            console.error('Failed to save to localStorage:', e);
          }
        }
      })();
      
      // Don't await - let it run in background, we'll navigate immediately
      // This prevents storage from blocking navigation
      savePromise.catch(err => console.warn('Background save failed:', err));

      // Clear pending outline and generation context
      console.log('Step 4: Cleaning up...');
      localStorage.removeItem('pending_outline');
      localStorage.removeItem('outline_generation_context');

      // Navigate to writer with structure mode enabled
      console.log('Step 3: Navigating to writer page...');
      console.log('Draft ID:', draftId);
      console.log('Current pathname:', window.location.pathname);
      
      const overallTime = performance.now() - overallStart;
      console.log(`Total approval time: ${overallTime.toFixed(2)}ms`);
      
      // Store draftId in state for navigation
      // Also save documentState to a temporary location that the writer page can access
      (window as any).__pendingDocumentState = documentState;
      (window as any).__pendingDraftId = draftId;
      
      // Navigate immediately - no delay needed
      console.log('Calling navigate...');
      navigate('/', {
        state: {
          structureMode: true,
          draftId,
          documentState, // Pass state directly in navigation
        },
        replace: false,
      });
      
      console.log('Navigation called successfully');
    } catch (error: any) {
      console.error('Failed to convert outline:', error);
      console.error('Error stack:', error.stack);
      console.error('Error details:', {
        message: error.message,
        name: error.name,
        stack: error.stack,
      });
      alert(`Failed to convert outline: ${error.message || 'Unknown error'}. Please check the console for details.`);
      setIsApproving(false);
    }
  };

  const handleCancel = () => {
    localStorage.removeItem('pending_outline');
    localStorage.removeItem('outline_generation_context');
    navigate('/writer', { replace: true });
  };

  if (loading || isGenerating) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-600 mb-4">
            {isGenerating ? generationProgress || 'Generating outline...' : 'Loading...'}
          </div>
          {isGenerating && (
            <div className="w-64 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 animate-pulse" style={{ width: '60%' }}></div>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!outline) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">No Outline Found</h2>
          <p className="text-gray-600 mb-6">No outline data available to preview.</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => navigate('/writer')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Go to Writer
            </button>
            {location.state?.generateOutline && (
              <button
                onClick={generateOutline}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Generate Outline
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

      return (
        <OutlinePreview
          outline={outline}
          onApprove={handleApprove}
          onCancel={handleCancel}
          isApproving={isApproving}
        />
      );
}

