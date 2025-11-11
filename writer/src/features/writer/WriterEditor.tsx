import { useEffect, useRef, useCallback } from 'react';
import { storage } from '../../lib/storage';
import { fileIO } from '../../lib/fileIO';

interface WriterEditorProps {
  title: string;
  content: string;
  onTitleChange: (title: string) => void;
  onContentChange: (content: string) => void;
  onCursorChange: (pos: number) => void;
  onSelectionChange: (selection: string) => void;
  inlineSuggestion: string;
  onAcceptSuggestion: () => void;
  onDismissSuggestion: () => void;
  showInlineSuggestion: boolean;
  isStreaming: boolean;
  streamingText: string;
  onSaveVersion: () => void;
  draftId: string;
  monospace: boolean;
  focusMode: boolean;
}

export default function WriterEditor({
  title,
  content,
  onTitleChange,
  onContentChange,
  onCursorChange,
  onSelectionChange,
  inlineSuggestion,
  onAcceptSuggestion,
  onDismissSuggestion,
  showInlineSuggestion,
  isStreaming,
  streamingText,
  onSaveVersion,
  draftId,
  monospace,
  focusMode,
}: WriterEditorProps) {
  const titleRef = useRef<HTMLInputElement>(null);
  const contentRef = useRef<HTMLTextAreaElement>(null);
  const suggestionRef = useRef<HTMLDivElement>(null);
  const autosaveTimeoutRef = useRef<number | null>(null);
  const lastContentRef = useRef(content);

  // Autosave
  useEffect(() => {
    if (content !== lastContentRef.current && draftId) {
      if (autosaveTimeoutRef.current !== null) {
        window.clearTimeout(autosaveTimeoutRef.current);
      }

      autosaveTimeoutRef.current = window.setTimeout(async () => {
        await storage.saveDraft(draftId, title, content);
        onSaveVersion();
        lastContentRef.current = content;
      }, 10000); // 10 seconds

      return () => {
        if (autosaveTimeoutRef.current !== null) {
          window.clearTimeout(autosaveTimeoutRef.current);
        }
      };
    }
  }, [content, title, draftId, onSaveVersion]);

  // Autosave on blur
  const handleBlur = useCallback(async () => {
    if (draftId && content !== lastContentRef.current) {
      await storage.saveDraft(draftId, title, content);
      onSaveVersion();
      lastContentRef.current = content;
    }
  }, [draftId, title, content, onSaveVersion]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        handleOpen();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        // Open command palette (handled by parent)
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSave = async () => {
    const name = title || 'untitled.txt';
    await fileIO.saveFile(name.endsWith('.txt') ? name : `${name}.txt`, content);
  };

  const handleOpen = async () => {
    const file = await fileIO.openFile();
    if (file) {
      onTitleChange(file.name.replace('.txt', ''));
      onContentChange(file.content);
    }
  };

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    onContentChange(newContent);

    // Update cursor position
    const pos = e.target.selectionStart;
    onCursorChange(pos);

    // Update selection
    const selection = window.getSelection()?.toString() || '';
    if (selection) {
      onSelectionChange(selection);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab' && showInlineSuggestion && inlineSuggestion) {
      e.preventDefault();
      onAcceptSuggestion();
    } else if (e.key === 'Escape' && showInlineSuggestion) {
      e.preventDefault();
      onDismissSuggestion();
    } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      // Continue writing (handled by parent)
    }
  };

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  const charCount = content.length;
  const readingTime = Math.ceil(wordCount / 200); // Assuming 200 words per minute

  return (
    <div className={`flex flex-col h-full ${focusMode ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      {/* Header */}
      {!focusMode && (
        <div className="border-b p-4 bg-white">
          <input
            ref={titleRef}
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="Document Title"
            className="text-2xl font-bold w-full outline-none border-none"
            aria-label="Document title"
          />
          <div className="flex gap-4 mt-2 text-sm text-gray-500">
            <span>{wordCount} words</span>
            <span>{charCount} characters</span>
            <span>~{readingTime} min read</span>
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="flex-1 relative overflow-auto bg-white">
        <div className="relative w-full h-full">
          {/* Mirror div for showing suggestion inline - behind textarea */}
          {showInlineSuggestion && !isStreaming && inlineSuggestion && (
            <div
              ref={suggestionRef}
              className={`absolute top-0 left-0 w-full h-full p-6 pointer-events-none z-0 ${
                monospace ? 'font-mono' : ''
              }`}
              style={{ fontSize: '16px', lineHeight: '1.6', whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}
            >
              <span className="text-gray-900">{content}</span>
              <span className="text-gray-400 italic opacity-70">
                {inlineSuggestion}
                <span className="text-xs ml-2 text-gray-500 opacity-60">(Tab to accept, Esc to dismiss)</span>
              </span>
            </div>
          )}

          {/* Streaming text - show inline after cursor */}
          {isStreaming && streamingText && (
            <div
              className={`absolute top-0 left-0 w-full h-full p-6 pointer-events-none z-0 ${
                monospace ? 'font-mono' : ''
              }`}
              style={{ fontSize: '16px', lineHeight: '1.6', whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}
            >
              <span className="text-gray-900">{content}</span>
              <span className="text-gray-400 italic opacity-70">{streamingText}</span>
            </div>
          )}

          {/* Textarea - transparent text, shows suggestion behind */}
          <textarea
            ref={contentRef}
            value={content}
            onChange={handleContentChange}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            onSelect={() => {
              const selection = window.getSelection()?.toString() || '';
              onSelectionChange(selection);
            }}
            className={`w-full h-full p-6 outline-none resize-none bg-transparent relative z-10 ${
              monospace ? 'font-mono' : ''
            }`}
            style={{ 
              fontSize: '16px', 
              lineHeight: '1.6', 
              color: showInlineSuggestion && !isStreaming ? 'transparent' : 'inherit',
              caretColor: '#000'
            }}
            placeholder="Start writing..."
            aria-label="Document content"
          />
        </div>
      </div>
    </div>
  );
}

