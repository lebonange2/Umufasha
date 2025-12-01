import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import WriterEditor from '../../features/writer/WriterEditor';
import AIToolbox from '../../features/writer/AIToolbox';
import DocumentManager from '../../features/writer/DocumentManager';
import StructureView from '../../features/structure/StructureView';
import { LLMAdapter } from '../../lib/llmAdapter';
import { storage } from '../../lib/storage';
import { fileIO } from '../../lib/fileIO';
import { buildSystemPrompt, buildUserPrompt, getRecentContext } from '../../features/writer/promptBuilders';
import { WriterMode, WriterSettings, Version } from '../../lib/types';
import { structureStorage } from '../../features/structure/storage';

const DEFAULT_SETTINGS: WriterSettings = {
  provider: 'openai',
  model: 'gpt-4o',
  temperature: 0.7,
  maxTokens: 1000,
  sendFullContext: false,
  respectOutline: false,
  safeMode: false,
};

// Load settings from localStorage on init
const loadSettings = (): WriterSettings => {
  try {
    const saved = localStorage.getItem('writerSettings');
    if (saved) {
      const parsed = JSON.parse(saved);
      return { ...DEFAULT_SETTINGS, ...parsed };
    }
  } catch (e) {
    console.error('Failed to load settings:', e);
  }
  return DEFAULT_SETTINGS;
};

// Save settings to localStorage
const saveSettings = (settings: WriterSettings) => {
  try {
    localStorage.setItem('writerSettings', JSON.stringify(settings));
  } catch (e) {
    console.error('Failed to save settings:', e);
  }
};

export default function WriterPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [draftId, setDraftId] = useState<string>('');
  const [title, setTitle] = useState('Untitled');
  const [content, setContent] = useState('');
  const [cursorPos, setCursorPos] = useState(0);
  const [selectedText, setSelectedText] = useState('');
  const [inlineSuggestion, setInlineSuggestion] = useState('');
  const [showInlineSuggestion, setShowInlineSuggestion] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [settings, setSettings] = useState<WriterSettings>(loadSettings());
  
  // Save settings when they change
  useEffect(() => {
    saveSettings(settings);
  }, [settings]);
  const [toolboxCollapsed, setToolboxCollapsed] = useState(false);
  const [monospace, setMonospace] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [versions, setVersions] = useState<Version[]>([]);
  const [showVersions, setShowVersions] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [textContext, setTextContext] = useState('');
  const [showDocumentManager, setShowDocumentManager] = useState(false);
  const [structureMode, setStructureMode] = useState(
    location.state?.structureMode || false
  );
  
  // Check if we should enable structure mode from location state
  useEffect(() => {
    console.log('Location state changed:', location.state);
    
    // Handle content from preview approval
    if (location.state?.content && !location.state?.structureMode) {
      console.log('Content provided from preview approval');
      setContent(location.state.content);
      if (location.state.title) {
        setTitle(location.state.title);
      }
      // Clear the state to prevent re-applying on re-render
      window.history.replaceState({}, '', window.location.pathname);
    }
    
    // Handle structure mode toggle
    if (location.state?.structureMode !== undefined) {
      setStructureMode(location.state.structureMode);
      
      if (location.state.structureMode) {
        // Try to get saved structure draft ID, or use provided one, or create new
        const savedStructureDraft = localStorage.getItem('writer_current_structure_draft');
        const draftId = location.state.draftId || savedStructureDraft || `draft_${Date.now()}`;
        console.log('Enabling structure mode with draftId:', draftId);
        setDraftId(draftId);
        localStorage.setItem('writer_current_structure_draft', draftId);
        
        // If documentState is passed directly, save it immediately
        if (location.state?.documentState) {
          console.log('Document state provided in navigation, saving...');
          structureStorage.init().then(async () => {
            await structureStorage.saveStructuredDraft(draftId, location.state.documentState);
            console.log('Document state saved');
          }).catch((err: any) => {
            console.warn('Failed to save document state:', err);
            // Fallback to localStorage
            try {
              localStorage.setItem(`writer_structure_${draftId}`, JSON.stringify({ 
                id: draftId, 
                state: location.state.documentState, 
                updatedAt: Date.now() 
              }));
            } catch (e) {
              console.error('Failed to save to localStorage:', e);
            }
          });
        }
      } else {
        // When disabling structure mode, save current writer content
        if (draftId && (title || content)) {
          storage.saveDraft(draftId, title, content).then(() => {
            localStorage.setItem('writer_current_draft', draftId);
            console.log('Writer content saved when exiting structure mode');
          }).catch(err => {
            console.error('Failed to save writer content:', err);
          });
        }
      }
    }
  }, [location]);

  const llmAdapter = useRef(new LLMAdapter());
  const autocompleteTimeoutRef = useRef<number | null>(null);

  // Initialize storage and load saved content
  useEffect(() => {
    storage.init().then(async () => {
      // Try to load last draft ID from localStorage
      const lastDraftId = localStorage.getItem('writer_current_draft');
      if (lastDraftId) {
        const saved = await storage.getDraft(lastDraftId);
        if (saved) {
          setDraftId(lastDraftId);
          setTitle(saved.title);
          setContent(saved.content);
          console.log('Loaded saved draft:', lastDraftId);
          return;
        }
      }
      
      // Create new draft if no saved one found
      const newDraftId = `draft_${Date.now()}`;
      setDraftId(newDraftId);
      localStorage.setItem('writer_current_draft', newDraftId);
    });
  }, []);

  // Load versions
  useEffect(() => {
    if (draftId) {
      storage.getVersions(draftId).then(setVersions);
    }
  }, [draftId]);

  // Autosave content and title
  useEffect(() => {
    if (draftId && (title || content)) {
      const saveTimeout = setTimeout(async () => {
        try {
          await storage.saveDraft(draftId, title, content);
          localStorage.setItem('writer_current_draft', draftId);
          console.log('Content autosaved:', draftId);
        } catch (error) {
          console.error('Failed to autosave:', error);
        }
      }, 2000); // Save after 2 seconds of inactivity

      return () => clearTimeout(saveTimeout);
    }
  }, [draftId, title, content]);

  // Save immediately before page unload
  useEffect(() => {
    const handleBeforeUnload = async () => {
      if (draftId && (title || content)) {
        try {
          await storage.saveDraft(draftId, title, content);
          localStorage.setItem('writer_current_draft', draftId);
          // Also save to localStorage as backup
          localStorage.setItem(`writer_draft_${draftId}`, JSON.stringify({ 
            id: draftId, 
            title, 
            content, 
            updatedAt: Date.now() 
          }));
        } catch (error) {
          console.error('Failed to save on unload:', error);
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [draftId, title, content]);

  // Autocomplete on pause
  useEffect(() => {
    if (autocompleteTimeoutRef.current !== null) {
      window.clearTimeout(autocompleteTimeoutRef.current);
    }

    if (content && cursorPos > 0 && !isStreaming && !selectedText) {
      autocompleteTimeoutRef.current = window.setTimeout(async () => {
        const context = getRecentContext(content, cursorPos, 1200);
        try {
          const systemPrompt = buildSystemPrompt('autocomplete', settings);
          const userPrompt = buildUserPrompt('autocomplete', '', context, undefined);

          const response = await llmAdapter.current.complete({
            system: systemPrompt,
            prompt: userPrompt,
            context,
            document_context: selectedDocuments.length > 0 ? selectedDocuments : undefined,
            text_context: textContext.trim() || undefined,
            mode: 'autocomplete',
            provider: settings.provider,
            model: settings.model,
            params: {
              temperature: settings.temperature * 0.7, // Lower temp for autocomplete
              max_tokens: 50,
            },
            stream: false,
          });

          if (response) {
            setInlineSuggestion(response.trim());
            setShowInlineSuggestion(true);
          }
        } catch (error: any) {
          console.error('Autocomplete error:', error);
          // Show error message if it's about missing API key
          if (error?.message?.includes('API key')) {
            alert(`Setup Required: ${error.message}`);
          }
        }
      }, 600); // 600ms pause
    }

    return () => {
      if (autocompleteTimeoutRef.current !== null) {
        window.clearTimeout(autocompleteTimeoutRef.current);
      }
    };
  }, [content, cursorPos, isStreaming, selectedText, settings]);

  const handleAIAction = useCallback(
    async (mode: WriterMode, params?: Record<string, any>) => {
      if (isStreaming) return;

      // For outline mode, navigate to preview page immediately with context
      if (mode === 'outline') {
        // Save current content and settings for outline generation
        const context = settings.sendFullContext
          ? content
          : getRecentContext(content, cursorPos, 3000);
        
        localStorage.setItem('outline_generation_context', JSON.stringify({
          content: context,
          fullContent: content,
          settings,
          selectedDocuments,
          textContext,
        }));
        
        // Navigate to outline preview page
        navigate('/outline-preview', { 
          state: { 
            generateOutline: true,
            context,
          } 
        });
        return;
      }

      setIsStreaming(true);
      setStreamingText('');
      setShowInlineSuggestion(false);

      try {
        const context = settings.sendFullContext
          ? content
          : getRecentContext(content, cursorPos, mode === 'continue' ? 3000 : 1200);

        const systemPrompt = buildSystemPrompt(mode, settings);
        const userPrompt =
          mode === 'qa' && params?.question
            ? buildUserPrompt(mode, params.question, selectedText || context, params)
            : buildUserPrompt(mode, '', selectedText || context, params);

          const request = {
            system: systemPrompt,
            prompt: userPrompt,
            context: selectedText || context,
            document_context: selectedDocuments.length > 0 ? selectedDocuments : undefined,
            text_context: textContext.trim() || undefined,
            mode,
            provider: settings.provider,
            model: settings.model,
            params: {
              temperature: settings.temperature,
              max_tokens: settings.maxTokens,
              ...params,
            },
            stream: true,
          };

        let accumulatedText = '';

        for await (const chunk of llmAdapter.current.stream(request)) {
          if (chunk.error) {
            // Show error in alert and console
            console.error('LLM Error:', chunk.error);
            alert(`AI Error: ${chunk.error}`);
            break;
          }

          if (chunk.done) break;

          accumulatedText += chunk.token;
          setStreamingText(accumulatedText);
        }

        // Insert the generated text
        if (accumulatedText && mode === 'continue') {
          const beforeCursor = content.slice(0, cursorPos);
          const afterCursor = content.slice(cursorPos);
          const newContent = beforeCursor + accumulatedText + afterCursor;
          setContent(newContent);
          setCursorPos(beforeCursor.length + accumulatedText.length);
        } else if (accumulatedText && selectedText && (mode === 'expand' || mode === 'rewrite')) {
          // Replace selection
          const start = content.indexOf(selectedText);
          if (start !== -1) {
            const before = content.slice(0, start);
            const after = content.slice(start + selectedText.length);
            const newContent = before + accumulatedText + after;
            setContent(newContent);
            setCursorPos(before.length + accumulatedText.length);
          }
        } else if (accumulatedText) {
          // Insert at cursor
          const beforeCursor = content.slice(0, cursorPos);
          const afterCursor = content.slice(cursorPos);
          const newContent = beforeCursor + accumulatedText + afterCursor;
          setContent(newContent);
          setCursorPos(beforeCursor.length + accumulatedText.length);
        }

        setStreamingText('');
      } catch (error: any) {
        console.error('AI action error:', error);
        alert(`Error: ${error.message}`);
      } finally {
        setIsStreaming(false);
      }
    },
    [content, cursorPos, selectedText, settings, isStreaming]
  );

  const handleStop = useCallback(() => {
    llmAdapter.current.abort();
    setIsStreaming(false);
    setStreamingText('');
  }, []);

  const handleAcceptSuggestion = useCallback(() => {
    if (inlineSuggestion) {
      const beforeCursor = content.slice(0, cursorPos);
      const afterCursor = content.slice(cursorPos);
      const newContent = beforeCursor + inlineSuggestion + ' ' + afterCursor;
      setContent(newContent);
      setCursorPos(beforeCursor.length + inlineSuggestion.length + 1);
      setInlineSuggestion('');
      setShowInlineSuggestion(false);
    }
  }, [content, cursorPos, inlineSuggestion]);

  const handleSaveVersion = useCallback(async () => {
    if (draftId) {
      await storage.saveVersion(draftId, content);
      const newVersions = await storage.getVersions(draftId);
      setVersions(newVersions);
    }
  }, [draftId, content]);

  const handleRestoreVersion = useCallback(
    async (version: Version) => {
      setContent(version.content);
      await storage.saveDraft(draftId, title, version.content);
    },
    [draftId, title]
  );

  const handleOpen = useCallback(async () => {
    const file = await fileIO.openFile();
    if (file) {
      setTitle(file.name.replace('.txt', ''));
      setContent(file.content);
      const newDraftId = `draft_${Date.now()}`;
      setDraftId(newDraftId);
      await storage.saveDraft(newDraftId, file.name.replace('.txt', ''), file.content);
    }
  }, []);

  const handleSave = useCallback(async () => {
    const name = title || 'untitled.txt';
    await fileIO.saveFile(name.endsWith('.txt') ? name : `${name}.txt`, content);
  }, [title, content]);

  // Show structure view if enabled
  if (structureMode) {
    // Get the saved structure draft ID to ensure consistency
    const savedStructureDraft = localStorage.getItem('writer_current_structure_draft');
    const structureDraftId = draftId || savedStructureDraft || `draft_${Date.now()}`;
    
    // Ensure it's saved
    if (structureDraftId && structureDraftId !== savedStructureDraft) {
      localStorage.setItem('writer_current_structure_draft', structureDraftId);
    }
    
    return (
      <StructureView
        draftId={structureDraftId}
        monospace={monospace}
        focusMode={focusMode}
        initialState={location.state?.documentState}
      />
    );
  }

  return (
    <div className="flex h-screen bg-white">
      {/* Main Editor */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <div className="border-b p-2 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-2">
            <button
              onClick={handleOpen}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              aria-label="Open file"
            >
              Open
            </button>
            <button
              onClick={handleSave}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              aria-label="Save file"
            >
              Save
            </button>
            <button
              onClick={() => setShowVersions(!showVersions)}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              aria-label="Version history"
            >
              History
            </button>
          </div>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={monospace}
                onChange={(e) => setMonospace(e.target.checked)}
              />
              Monospace
            </label>
            <button
              onClick={() => setFocusMode(!focusMode)}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              aria-label="Focus mode"
            >
              Focus
            </button>
            <button
              onClick={() => setStructureMode(!structureMode)}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              aria-label="Structure mode"
            >
              {structureMode ? 'Simple' : 'Structure'}
            </button>
            <button
              onClick={() => {
                // Test outline preview - check if there's a pending outline
                const pendingOutline = localStorage.getItem('pending_outline');
                if (pendingOutline) {
                  navigate('/outline-preview');
                } else {
                  alert('No outline found. Generate an outline first using the AI "Outline" feature, or paste outline JSON into localStorage with key "pending_outline"');
                }
              }}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              aria-label="Preview outline"
              title="Preview outline (if available)"
            >
              Preview Outline
            </button>
          </div>
        </div>

        {/* Version history sidebar */}
        {showVersions && (
          <div className="absolute left-0 top-12 w-64 h-[calc(100vh-3rem)] bg-white border-r shadow-lg z-10 overflow-y-auto">
            <div className="p-4 border-b">
              <h3 className="font-semibold">Version History</h3>
            </div>
            <div className="p-2">
              {versions.map((version) => (
                <button
                  key={version.id}
                  onClick={() => handleRestoreVersion(version)}
                  className="w-full text-left p-2 hover:bg-gray-100 rounded mb-1"
                >
                  <div className="text-sm font-medium">
                    {new Date(version.createdAt).toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {version.content.slice(0, 50)}...
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        <WriterEditor
          title={title}
          content={content}
          onTitleChange={setTitle}
          onContentChange={setContent}
          onCursorChange={setCursorPos}
          onSelectionChange={setSelectedText}
          inlineSuggestion={inlineSuggestion}
          onAcceptSuggestion={handleAcceptSuggestion}
          onDismissSuggestion={() => {
            setShowInlineSuggestion(false);
            setInlineSuggestion('');
          }}
          showInlineSuggestion={showInlineSuggestion}
          isStreaming={isStreaming}
          streamingText={streamingText}
          onSaveVersion={handleSaveVersion}
          draftId={draftId}
          monospace={monospace}
          focusMode={focusMode}
        />
      </div>

      {/* AI Toolbox */}
      <div className="flex flex-col h-full">
        <AIToolbox
          settings={settings}
          onSettingsChange={setSettings}
          onAction={handleAIAction}
          isStreaming={isStreaming}
          onStop={handleStop}
          collapsed={toolboxCollapsed}
          onToggleCollapse={() => setToolboxCollapsed(!toolboxCollapsed)}
          selectedText={selectedText}
          hasSelection={!!selectedText}
          showDocumentManager={showDocumentManager}
          onToggleDocumentManager={() => setShowDocumentManager(!showDocumentManager)}
          selectedDocumentsCount={selectedDocuments.length}
        />

        {/* Document Manager Panel */}
        {showDocumentManager && !toolboxCollapsed && (
          <div className="border-t bg-white p-4 overflow-y-auto max-h-96">
            <DocumentManager
              selectedDocuments={selectedDocuments}
              onDocumentsChange={setSelectedDocuments}
              textContext={textContext}
              onTextContextChange={setTextContext}
            />
          </div>
        )}
      </div>
    </div>
  );
}

