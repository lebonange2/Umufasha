import { useEffect, useMemo, useRef, useState } from 'react';
import './ChatPanel.css';

type ChatRole = 'user' | 'assistant';

type ChatMessage = {
  role: ChatRole;
  content: string;
};

type AgentStep =
  | { type: 'assistant'; content: string }
  | { type: 'tool'; tool: string; params: Record<string, any>; result: any };

interface ChatPanelProps {
  model: string;
  cwsConnected: boolean;
  onFileTouched?: (path: string) => void;
}

export default function ChatPanel({ model, cwsConnected, onFileTouched }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Tell me what you want to build. I can help plan, generate code changes, and (when connected) use workspace tools to read/write files and run commands.",
    },
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy]);

  const canSend = useMemo(() => input.trim().length > 0 && !busy, [input, busy]);

  async function send() {
    if (!canSend) return;
    const userText = input.trim();
    setInput('');
    setBusy(true);
    setSteps([]);
    setMessages((prev) => [...prev, { role: 'user', content: userText }]);

    try {
      const payload = {
        model: model || 'llama3:latest',
        messages: [...messages, { role: 'user', content: userText }].map((m) => ({
          role: m.role,
          content: m.content,
        })),
        max_steps: 5,
      };

      const resp = await fetch('/api/coding-environment/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      const output = data.output || '';
      const agentSteps = (data.steps || []) as AgentStep[];
      setSteps(agentSteps);

      // If the agent touched files (create/write), refresh/open them in the UI like Cursor.
      try {
        const touched: string[] = [];
        for (const s of agentSteps) {
          if (s.type === 'tool' && (s.tool === 'fs.write' || s.tool === 'fs.create')) {
            const p = (s.params || {}).path;
            if (typeof p === 'string' && p.length > 0) touched.push(p);
          }
        }
        if (touched.length > 0 && onFileTouched) {
          onFileTouched(touched[touched.length - 1]);
        }
      } catch {
        // ignore
      }

      if (output.trim().length > 0) {
        setMessages((prev) => [...prev, { role: 'assistant', content: output }]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content:
              'I did not return a final message. If I called tools, check the step log; then ask me what to do next.',
          },
        ]);
      }
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            `Error: ${e?.message || 'Unknown error'}\n\n` +
            `Tips:\n- Ensure Ollama is running: ollama serve\n- Ensure the selected model is pulled (e.g. ollama pull llama3)\n`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-title">Agent Chat</div>
        <div className="chat-meta">
          <span className="chat-pill">Model: {model || 'llama3:latest'}</span>
          <span className={`chat-pill ${cwsConnected ? 'ok' : 'warn'}`}>
            Tools: {cwsConnected ? 'ready' : 'limited'}
          </span>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-message ${m.role}`}>
            <div className="chat-role">{m.role === 'user' ? 'You' : 'Agent'}</div>
            <div className="chat-content">{m.content}</div>
          </div>
        ))}
        {busy && (
          <div className="chat-message assistant">
            <div className="chat-role">Agent</div>
            <div className="chat-content">Thinking…</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {steps.length > 0 && (
        <details className="chat-steps" open>
          <summary>Steps ({steps.length})</summary>
          <div className="chat-steps-body">
            {steps.map((s, i) => (
              <div key={i} className="chat-step">
                {s.type === 'tool' ? (
                  <>
                    <div className="chat-step-title">
                      tool: <code>{s.tool}</code>
                    </div>
                    <pre className="chat-step-pre">{JSON.stringify({ params: s.params, result: s.result }, null, 2)}</pre>
                  </>
                ) : (
                  <>
                    <div className="chat-step-title">assistant</div>
                    <pre className="chat-step-pre">{s.content}</pre>
                  </>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe what you want to build…"
          rows={3}
          disabled={busy}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button onClick={send} disabled={!canSend}>
          Send
        </button>
      </div>
    </div>
  );
}

