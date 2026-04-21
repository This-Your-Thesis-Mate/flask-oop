-- Add ref_module_id column to modules table
-- This is the user-provided module ID (not the internal database ID)

ALTER TABLE modules 
ADD COLUMN IF NOT EXISTS ref_module_id integer;

-- Add comment
COMMENT ON COLUMN modules.ref_module_id IS 'User-provided module ID for external reference';
