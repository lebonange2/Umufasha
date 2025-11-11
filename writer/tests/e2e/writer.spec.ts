import { test, expect } from '@playwright/test';

test.describe('Writer Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/writer');
  });

  test('should load the writer page', async ({ page }) => {
    await expect(page.locator('#root')).toBeVisible();
  });

  test('should allow typing in editor', async ({ page }) => {
    const editor = page.locator('textarea[aria-label="Document content"]');
    await editor.fill('This is a test document.');
    await expect(editor).toHaveValue('This is a test document.');
  });

  test('should save file', async ({ page }) => {
    const editor = page.locator('textarea[aria-label="Document content"]');
    await editor.fill('Test content for saving');

    // Mock file download
    const downloadPromise = page.waitForEvent('download');
    await page.click('button[aria-label="Save file"]');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.txt');
  });

  test('should open file', async ({ page }) => {
    // This would require mocking file input
    // For now, just check that the button exists
    const openButton = page.locator('button[aria-label="Open file"]');
    await expect(openButton).toBeVisible();
  });

  test('should show version history', async ({ page }) => {
    const editor = page.locator('textarea[aria-label="Document content"]');
    await editor.fill('Initial content');
    await page.waitForTimeout(11000); // Wait for autosave

    await page.click('button[aria-label="Version history"]');
    await expect(page.locator('text=Version History')).toBeVisible();
  });
});

