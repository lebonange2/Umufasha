import { describe, it, expect } from 'vitest';
import { buildSystemPrompt, buildUserPrompt, getRecentContext } from '../../src/features/writer/promptBuilders';
import { WriterMode, WriterSettings } from '../../src/lib/types';

describe('promptBuilders', () => {
  const defaultSettings: WriterSettings = {
    model: 'gpt-4o',
    temperature: 0.7,
    maxTokens: 1000,
    sendFullContext: false,
    respectOutline: false,
    safeMode: false,
  };

  describe('buildSystemPrompt', () => {
    it('should build system prompt for autocomplete', () => {
      const prompt = buildSystemPrompt('autocomplete', defaultSettings);
      expect(prompt).toContain('Complete the current sentence');
    });

    it('should include safe mode warning when enabled', () => {
      const settings = { ...defaultSettings, safeMode: true };
      const prompt = buildSystemPrompt('autocomplete', settings);
      expect(prompt).toContain('Safe mode');
    });
  });

  describe('buildUserPrompt', () => {
    it('should build user prompt for autocomplete', () => {
      const prompt = buildUserPrompt('autocomplete', '', 'Some context', undefined);
      expect(prompt).toContain('Context:');
      expect(prompt).toContain('Some context');
    });

    it('should build user prompt for expand with target words', () => {
      const prompt = buildUserPrompt('expand', '', 'Selected text', { target_words: 150 });
      expect(prompt).toContain('150 words');
      expect(prompt).toContain('Selected text');
    });

    it('should build user prompt for rewrite with tone', () => {
      const prompt = buildUserPrompt('rewrite', '', 'Selected text', { tone: 'vivid' });
      expect(prompt).toContain('vivid');
      expect(prompt).toContain('Selected text');
    });
  });

  describe('getRecentContext', () => {
    it('should return recent context from cursor position', () => {
      const text = 'This is a long text that we want to get context from.';
      const context = getRecentContext(text, text.length, 20);
      expect(context.length).toBeLessThanOrEqual(20);
      expect(context).toContain('context from');
    });

    it('should handle cursor at start', () => {
      const text = 'Some text';
      const context = getRecentContext(text, 0, 100);
      expect(context).toBe('');
    });

    it('should respect maxChars limit', () => {
      const text = 'a'.repeat(1000);
      const context = getRecentContext(text, 1000, 100);
      expect(context.length).toBeLessThanOrEqual(100);
    });
  });
});

