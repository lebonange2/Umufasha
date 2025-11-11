import { WriterMode, WriterSettings } from '../../lib/types';

export function buildSystemPrompt(mode: WriterMode, settings: WriterSettings): string {
  const base = `You are a concise, structure-aware book writing assistant. 
Honor user voice and preserve factual details. 
Never fabricate citations. Avoid repetition. 
When asked to continue, maintain tense, POV, and style of the last 50 tokens.`;

  const modeSpecific: Record<WriterMode, string> = {
    autocomplete: 'Complete the current sentence naturally in <= 40 words. Return only the completion, no preface.',
    continue: 'Continue this draft for ~150–250 words, matching tone and POV. Avoid repeating the last lines. Introduce 1 new concrete detail.',
    expand: 'Expand the selection to the target word count, preserving meaning and style.',
    summarize: 'Provide a brief, accurate summary of the selection.',
    outline: 'Produce a hierarchical outline (Chapters > Sections > Beats) from the draft. Return JSON with: title, chapters[{title, summary, sections[{title, beats[]}] }].',
    rewrite: 'Rewrite the selection in the requested tone. Keep facts. Return text only.',
    qa: 'Answer questions about the selection concisely and accurately.',
  };

  let prompt = `${base}\n\n${modeSpecific[mode]}`;

  if (settings.safeMode) {
    prompt += '\n\nSafe mode: Do not generate explicit, violent, or inappropriate content.';
  }

  return prompt;
}

export function buildUserPrompt(
  mode: WriterMode,
  prompt: string,
  context: string | undefined,
  params: Record<string, any> | undefined
): string {
  switch (mode) {
    case 'autocomplete':
      return `Context:\n${context || ''}\n\nComplete the current sentence:`;

    case 'continue':
      return `Context:\n${context || ''}\n\nContinue writing:`;

    case 'expand':
      const targetWords = params?.target_words || 100;
      return `Expand the selection to ~${targetWords} words, preserving meaning and style.\n\nSelection:\n${context || ''}`;

    case 'summarize':
      return `Summarize this section:\n\n${context || ''}`;

    case 'outline':
      return `Draft:\n${context || prompt}\n\nGenerate an outline:`;

    case 'rewrite':
      const tone = params?.tone || 'plain';
      return `Rewrite the selection in the style: ${tone}. Keep facts. Return text only.\n\nSelection:\n${context || ''}`;

    case 'qa':
      return `Context:\n${context || ''}\n\nQuestion: ${prompt}\n\nAnswer:`;

    default:
      return context ? `${prompt}\n\nContext:\n${context}` : prompt;
  }
}

export function getRecentContext(
  text: string,
  cursorPos: number,
  maxChars: number = 1200
): string {
  const start = Math.max(0, cursorPos - maxChars);
  return text.slice(start, cursorPos);
}

