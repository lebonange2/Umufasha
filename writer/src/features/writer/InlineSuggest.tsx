import { useEffect } from 'react';

interface InlineSuggestProps {
  suggestion: string;
  onAccept: () => void;
  onDismiss: () => void;
  visible: boolean;
}

export default function InlineSuggest({ suggestion, onAccept, onDismiss, visible }: InlineSuggestProps) {

  useEffect(() => {
    if (visible && suggestion) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Tab' && !e.shiftKey) {
          e.preventDefault();
          onAccept();
        } else if (e.key === 'Escape') {
          onDismiss();
        }
      };

      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [visible, suggestion, onAccept, onDismiss]);

  // This component is now just for keyboard handling
  // The actual rendering is done in WriterEditor
  return null;
}

