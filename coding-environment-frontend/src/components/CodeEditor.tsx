import { Editor } from '@monaco-editor/react';
import './CodeEditor.css';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: string;
  readOnly?: boolean;
}

export default function CodeEditor({ value, onChange, language, readOnly = false }: CodeEditorProps) {
  return (
    <div className="code-editor">
      <Editor
        height="100%"
        language={language}
        value={value}
        onChange={(val) => onChange(val || '')}
        theme="vs-dark"
        options={{
          readOnly,
          minimap: { enabled: true },
          fontSize: 14,
          lineNumbers: 'on',
          roundedSelection: false,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
          wordWrap: 'on',
        }}
      />
    </div>
  );
}
