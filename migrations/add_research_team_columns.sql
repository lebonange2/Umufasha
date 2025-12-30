-- Migration: Add Research Team columns to core_devices_projects table
-- Date: 2025-12-30
-- Purpose: Support Research Mode feature

-- Add research_mode column
ALTER TABLE core_devices_projects 
ADD COLUMN IF NOT EXISTS research_mode BOOLEAN DEFAULT FALSE;

-- Add research_scope column
ALTER TABLE core_devices_projects 
ADD COLUMN IF NOT EXISTS research_scope TEXT;

-- Add pdf_report column (binary storage for PDF files)
ALTER TABLE core_devices_projects 
ADD COLUMN IF NOT EXISTS pdf_report BYTEA;

-- Make product_idea nullable (was required before)
ALTER TABLE core_devices_projects 
ALTER COLUMN product_idea DROP NOT NULL;

-- Add comment
COMMENT ON COLUMN core_devices_projects.research_mode IS 'Enable Research Team to discover product opportunities';
COMMENT ON COLUMN core_devices_projects.research_scope IS 'Optional focus area for research (e.g., health, energy)';
COMMENT ON COLUMN core_devices_projects.pdf_report IS 'Generated PDF research report (binary data)';
