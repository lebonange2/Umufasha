import { describe, it, expect, beforeEach } from 'vitest';
import { Storage } from '../../src/lib/storage';

describe('Storage', () => {
  let storage: Storage;

  beforeEach(async () => {
    storage = new Storage();
    // Mock IndexedDB or use localStorage fallback
  });

  it('should save and retrieve draft', async () => {
    const id = 'test_draft';
    const title = 'Test Draft';
    const content = 'Test content';

    await storage.saveDraft(id, title, content);
    const draft = await storage.getDraft(id);

    expect(draft).not.toBeNull();
    expect(draft?.title).toBe(title);
    expect(draft?.content).toBe(content);
  });

  it('should list drafts', async () => {
    await storage.saveDraft('draft1', 'Draft 1', 'Content 1');
    await storage.saveDraft('draft2', 'Draft 2', 'Content 2');

    const drafts = await storage.listDrafts();
    expect(drafts.length).toBeGreaterThanOrEqual(2);
  });

  it('should save and retrieve versions', async () => {
    const draftId = 'test_draft';
    const content1 = 'Version 1';
    const content2 = 'Version 2';

    // Add a small delay to ensure different timestamps
    await storage.saveVersion(draftId, content1);
    await new Promise(resolve => setTimeout(resolve, 10));
    await storage.saveVersion(draftId, content2);

    const versions = await storage.getVersions(draftId);
    expect(versions.length).toBeGreaterThanOrEqual(2);
    // Versions should be sorted by createdAt descending (most recent first)
    const sortedVersions = versions.sort((a, b) => b.createdAt - a.createdAt);
    expect(sortedVersions[0].content).toBe(content2);
  });
});

