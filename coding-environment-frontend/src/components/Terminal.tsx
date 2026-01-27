import { useState, useRef, useEffect } from 'react';
import { CWSClient } from '../services/cwsClient';
import './Terminal.css';

interface TerminalProps {
  cwsClient: CWSClient | null;
}

export default function Terminal({ cwsClient }: TerminalProps) {
  const [output, setOutput] = useState<string>('');
  const [command, setCommand] = useState<string>('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || !cwsClient?.isConnected()) return;

    const cmd = command.trim();
    setHistory(prev => [...prev, cmd]);
    setHistoryIndex(-1);
    setOutput(prev => prev + `$ ${cmd}\n`);
    setCommand('');

    try {
      const [cmdName, ...args] = cmd.split(' ');
      const result = await cwsClient.runCommand(cmdName, args);
      setOutput(prev => prev + result + '\n');
    } catch (error) {
      setOutput(prev => prev + `Error: ${error instanceof Error ? error.message : 'Unknown error'}\n`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length > 0) {
        const newIndex = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setCommand(history[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex !== -1) {
        const newIndex = historyIndex + 1;
        if (newIndex >= history.length) {
          setHistoryIndex(-1);
          setCommand('');
        } else {
          setHistoryIndex(newIndex);
          setCommand(history[newIndex]);
        }
      }
    }
  };

  return (
    <div className="terminal">
      <div className="terminal-header">Terminal</div>
      <div className="terminal-output" ref={terminalRef}>
        {output || <div className="terminal-prompt">Terminal ready. Type a command...</div>}
      </div>
      <form onSubmit={handleSubmit} className="terminal-input-form">
        <span className="terminal-prompt">$</span>
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          className="terminal-input"
          placeholder={cwsClient?.isConnected() ? "Enter command..." : "CWS not connected"}
          disabled={!cwsClient?.isConnected()}
        />
      </form>
    </div>
  );
}
