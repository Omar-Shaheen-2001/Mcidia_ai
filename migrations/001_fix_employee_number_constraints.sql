-- Migration: Fix Employee Number Constraints for Multi-Tenant Support
-- Date: 2025-11-13
-- Purpose: Change employee_number unique constraint from global to per-organization
--          and add sequence table for atomic number generation

-- Step 1: Drop old global unique constraint
-- This constraint prevented different organizations from using the same employee numbers
ALTER TABLE hr_employees DROP CONSTRAINT IF EXISTS hr_employees_employee_number_key;

-- Step 2: Add new composite unique constraint
-- This ensures employee numbers are unique within each organization, not globally
ALTER TABLE hr_employees ADD CONSTRAINT IF NOT EXISTS uq_org_employee_number 
    UNIQUE (organization_id, employee_number);

-- Step 3: Create sequence table for atomic employee number generation
-- This table stores the last used employee number for each organization
-- It enables atomic, concurrent-safe number generation without race conditions
CREATE TABLE IF NOT EXISTS employee_number_sequences (
    organization_id INTEGER PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
    last_number INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 4: Initialize sequence table with existing employee numbers
-- This ensures existing organizations start from their current max number
INSERT INTO employee_number_sequences (organization_id, last_number)
SELECT 
    organization_id,
    COALESCE(MAX(CAST(SUBSTRING(employee_number FROM 5) AS INTEGER)), 0) as last_number
FROM hr_employees
WHERE employee_number LIKE 'EMP-%'
GROUP BY organization_id
ON CONFLICT (organization_id) DO NOTHING;

-- Verification Queries (for manual testing):
-- SELECT conname, contype FROM pg_constraint WHERE conrelid = 'hr_employees'::regclass;
-- SELECT * FROM employee_number_sequences;
