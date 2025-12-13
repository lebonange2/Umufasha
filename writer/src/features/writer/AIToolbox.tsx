import { useState } from 'react';
import { WriterMode, WriterSettings } from '../../lib/types';

interface AIToolboxProps {
  settings: WriterSettings;
  onSettingsChange: (settings: WriterSettings) => void;
  onAction: (mode: WriterMode, params?: Record<string, any>) => void;
  isStreaming: boolean;
  onStop: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  selectedText: string;
  hasSelection: boolean;
  showDocumentManager: boolean;
  onToggleDocumentManager: () => void;
  selectedDocumentsCount: number;
}

export default function AIToolbox({
  settings,
  onSettingsChange,
  onAction,
  isStreaming,
  onStop,
  collapsed,
  onToggleCollapse,
  selectedText: _selectedText,
  hasSelection,
  showDocumentManager,
  onToggleDocumentManager,
  selectedDocumentsCount,
}: AIToolboxProps) {
  const [expandedAction, setExpandedAction] = useState<WriterMode | null>(null);
  const [expandWords, setExpandWords] = useState(100);
  const [rewriteTone, setRewriteTone] = useState('plain');
  const [qaQuestion, setQaQuestion] = useState('');

  const actions: Array<{
    mode: WriterMode;
    label: string;
    description: string;
    requiresSelection?: boolean;
  }> = [
    { mode: 'autocomplete', label: 'Autocomplete Sentence', description: 'Complete the current sentence' },
    { mode: 'continue', label: 'Continue Writing', description: 'Continue the current paragraph' },
    { mode: 'expand', label: 'Expand Selection', description: 'Expand selected text', requiresSelection: true },
    { mode: 'summarize', label: 'Summarize Section', description: 'Summarize selected text', requiresSelection: true },
    { mode: 'outline', label: 'Generate Outline', description: 'Create outline from draft' },
    { mode: 'rewrite', label: 'Rewrite Tone', description: 'Rewrite selection with different tone', requiresSelection: true },
    { mode: 'qa', label: 'Ask About This', description: 'Q&A about selection', requiresSelection: true },
  ];

  const handleAction = (mode: WriterMode) => {
    if (mode === 'expand') {
      onAction(mode, { target_words: expandWords });
    } else if (mode === 'rewrite') {
      onAction(mode, { tone: rewriteTone });
    } else if (mode === 'qa') {
      if (qaQuestion.trim()) {
        onAction(mode, { question: qaQuestion });
        setQaQuestion('');
      }
    } else {
      onAction(mode);
    }
    setExpandedAction(null);
  };

  return (
    <div
      className={`bg-gray-50 border-l transition-all duration-300 ${
        collapsed ? 'w-12' : 'w-80'
      } flex flex-col h-full`}
    >
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        {!collapsed && <h2 className="font-semibold">AI Toolbox</h2>}
        <button
          onClick={onToggleCollapse}
          className="p-2 hover:bg-gray-200 rounded"
          aria-label={collapsed ? 'Expand toolbox' : 'Collapse toolbox'}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      {!collapsed && (
        <>
          {/* Actions */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {actions.map((action) => {
              const disabled = action.requiresSelection && !hasSelection;
              const isExpanded = expandedAction === action.mode;

              return (
                <div key={action.mode} className="space-y-2">
                  <button
                    onClick={() => {
                      if (isExpanded) {
                        handleAction(action.mode);
                      } else {
                        setExpandedAction(action.mode);
                      }
                    }}
                    disabled={disabled || isStreaming}
                    className={`w-full text-left p-3 rounded border ${
                      disabled
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white hover:bg-gray-100'
                    } ${isStreaming ? 'opacity-50' : ''}`}
                    aria-label={action.label}
                  >
                    <div className="font-medium">{action.label}</div>
                    <div className="text-sm text-gray-500">{action.description}</div>
                  </button>

                  {/* Expanded options */}
                  {isExpanded && action.mode === 'expand' && (
                    <div className="ml-4 p-2 bg-white rounded border">
                      <label className="block text-sm mb-1">Target words:</label>
                      <input
                        type="number"
                        value={expandWords}
                        onChange={(e) => setExpandWords(Number(e.target.value))}
                        className="w-full p-1 border rounded"
                        min="50"
                        max="500"
                      />
                      <button
                        onClick={() => handleAction('expand')}
                        className="mt-2 w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                      >
                        Expand
                      </button>
                    </div>
                  )}

                  {isExpanded && action.mode === 'rewrite' && (
                    <div className="ml-4 p-2 bg-white rounded border">
                      <label className="block text-sm mb-1">Tone:</label>
                      <select
                        value={rewriteTone}
                        onChange={(e) => setRewriteTone(e.target.value)}
                        className="w-full p-1 border rounded"
                      >
                        <option value="plain">Plain</option>
                        <option value="vivid">Vivid</option>
                        <option value="academic">Academic</option>
                        <option value="humorous">Humorous</option>
                      </select>
                      <button
                        onClick={() => handleAction('rewrite')}
                        className="mt-2 w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                      >
                        Rewrite
                      </button>
                    </div>
                  )}

                  {isExpanded && action.mode === 'qa' && (
                    <div className="ml-4 p-2 bg-white rounded border">
                      <label className="block text-sm mb-1">Question:</label>
                      <textarea
                        value={qaQuestion}
                        onChange={(e) => setQaQuestion(e.target.value)}
                        className="w-full p-1 border rounded"
                        rows={3}
                        placeholder="Ask a question about the selection..."
                      />
                      <button
                        onClick={() => handleAction('qa')}
                        disabled={!qaQuestion.trim()}
                        className="mt-2 w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                      >
                        Ask
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Stop button */}
          {isStreaming && (
            <div className="p-4 border-t">
              <button
                onClick={onStop}
                className="w-full p-3 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Stop Generation
              </button>
            </div>
          )}

          {/* Document Manager Toggle */}
          <div className="p-4 border-t">
            <button
              onClick={onToggleDocumentManager}
              className={`w-full p-2 rounded border text-sm ${
                showDocumentManager
                  ? 'bg-blue-500 text-white border-blue-600'
                  : 'bg-white hover:bg-gray-100'
              }`}
            >
              <span className="flex items-center justify-center gap-2">
                📁 Documents & Context
                {selectedDocumentsCount > 0 && (
                  <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                    {selectedDocumentsCount}
                  </span>
                )}
              </span>
            </button>
          </div>

          {/* Settings */}
          <div className="p-4 border-t space-y-3">
            <h3 className="font-semibold text-sm">Settings</h3>

            {/* Model Selection - Local models only (Ollama) */}
            <div>
              <label className="block text-xs mb-1">Model (Local):</label>
              <select
                value={settings.model}
                onChange={(e) => onSettingsChange({ ...settings, model: e.target.value, provider: 'local' })}
                className="w-full p-1 border rounded text-sm"
              >
                <option value="qwen3:30b">Qwen3 30B</option>
                <option value="llama3:latest">Llama 3 (Latest)</option>
                <option value="llama3.2:latest">Llama 3.2 (Latest)</option>
                <option value="mistral:latest">Mistral (Latest)</option>
                <option value="codellama:latest">CodeLlama (Latest)</option>
                <option value="phi3:latest">Phi-3 (Latest)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs mb-1">
                Temperature: {settings.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) =>
                  onSettingsChange({ ...settings, temperature: Number(e.target.value) })
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-xs mb-1">Max Tokens:</label>
              <input
                type="number"
                value={settings.maxTokens}
                onChange={(e) =>
                  onSettingsChange({ ...settings, maxTokens: Number(e.target.value) })
                }
                className="w-full p-1 border rounded text-sm"
                min="100"
                max="4000"
              />
            </div>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.sendFullContext}
                onChange={(e) =>
                  onSettingsChange({ ...settings, sendFullContext: e.target.checked })
                }
              />
              <span className="text-xs">Send full context</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.respectOutline}
                onChange={(e) =>
                  onSettingsChange({ ...settings, respectOutline: e.target.checked })
                }
              />
              <span className="text-xs">Respect outline constraints</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.safeMode}
                onChange={(e) =>
                  onSettingsChange({ ...settings, safeMode: e.target.checked })
                }
              />
              <span className="text-xs">Safe mode</span>
            </label>
          </div>
        </>
      )}
    </div>
  );
}

