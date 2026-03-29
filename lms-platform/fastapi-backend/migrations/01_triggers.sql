-- Migration: 01_triggers.sql
-- Purpose: Add updated_at triggers to ensure data consistency

-- 1. Create a reusable function to update the 'updated_at' column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 2. Apply triggers to tables

-- Table: competency_mastery
-- Ensure the table exists before adding trigger (idempotent check not easily possible in pure SQL without DO block, but assuming table exists)
DROP TRIGGER IF EXISTS update_competency_mastery_updated_at ON competency_mastery;
CREATE TRIGGER update_competency_mastery_updated_at
    BEFORE UPDATE ON competency_mastery
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Table: notifications
DROP TRIGGER IF EXISTS update_notifications_updated_at ON notifications;
CREATE TRIGGER update_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Table: sba_records (Usually immutable, but if editable)
-- If sba_records has an updated_at column
-- DROP TRIGGER IF EXISTS update_sba_records_updated_at ON sba_records;
-- CREATE TRIGGER update_sba_records_updated_at
--     BEFORE UPDATE ON sba_records
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- Note: Run this script in the Supabase SQL Editor.
