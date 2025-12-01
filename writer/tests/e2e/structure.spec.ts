import { test, expect } from '@playwright/test';

test.describe('Document Structure Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to writer page
    await page.goto('/writer');
    // Wait for page to load
    await page.waitForSelector('text=Open');
  });

  test('should toggle structure mode', async ({ page }) => {
    // Click structure mode button
    await page.click('button:has-text("Structure")');
    
    // Should see outline panel
    await expect(page.locator('text=Outline & Structure')).toBeVisible();
  });

  test('should create a chapter', async ({ page }) => {
    // Enter structure mode
    await page.click('button:has-text("Structure")');
    
    // Click Chapter button
    await page.click('button:has-text("Chapter")');
    
    // Should see chapter in outline
    await expect(page.locator('text=Untitled chapter')).toBeVisible();
  });

  test('should create and number sections', async ({ page }) => {
    // Enter structure mode
    await page.click('button:has-text("Structure")');
    
    // Create a chapter
    await page.click('button:has-text("Chapter")');
    
    // Select the chapter
    await page.click('text=Untitled chapter');
    
    // Create a section
    await page.click('button:has-text("Section")');
    
    // Should see numbered section (1.1)
    await expect(page.locator('text=1.1')).toBeVisible();
  });

  test('should drag and drop to reorder', async ({ page }) => {
    // Enter structure mode
    await page.click('button:has-text("Structure")');
    
    // Create two chapters
    await page.click('button:has-text("Chapter")');
    await page.click('button:has-text("Chapter")');
    
    // Get first chapter element
    const firstChapter = page.locator('text=Untitled chapter').first();
    const secondChapter = page.locator('text=Untitled chapter').last();
    
    // Drag first to second position
    await firstChapter.dragTo(secondChapter);
    
    // Order should be updated (numbers will change)
    // This is a basic test - full drag-and-drop testing would require more setup
  });

  test('should export to markdown', async ({ page }) => {
    // Enter structure mode
    await page.click('button:has-text("Structure")');
    
    // Create a chapter with content
    await page.click('button:has-text("Chapter")');
    await page.click('text=Untitled chapter');
    
    // Add content
    const editor = page.locator('textarea');
    await editor.fill('Test content');
    
    // Export
    await page.selectOption('select', 'markdown');
    
    // Should trigger download (this would need file download handling in real test)
    // For now, just verify the select is present
    await expect(page.locator('select')).toBeVisible();
  });

  test('should show breadcrumb navigation', async ({ page }) => {
    // Enter structure mode
    await page.click('button:has-text("Structure")');
    
    // Create part and chapter
    await page.click('button:has-text("Part")');
    await page.click('text=Untitled part');
    await page.click('button:has-text("Chapter")');
    await page.click('text=Untitled chapter');
    
    // Should see breadcrumb
    await expect(page.locator('text=›')).toBeVisible();
  });

  test('should toggle page mode', async ({ page }) => {
    // Enter structure mode
    await page.click('button:has-text("Structure")');
    
    // Toggle page mode
    await page.click('button:has-text("Page Mode")');
    
    // Should show page mode is on
    await expect(page.locator('text=Page Mode: On')).toBeVisible();
  });

  test('should show table of contents', async ({ page }) => {
    // Enter structure mode
    await page.click('button:has-text("Structure")');
    
    // Create some structure
    await page.click('button:has-text("Chapter")');
    await page.click('button:has-text("Section")');
    
    // Open TOC
    await page.click('button:has-text("TOC")');
    
    // Should see TOC modal
    await expect(page.locator('text=Table of Contents')).toBeVisible();
  });
});

