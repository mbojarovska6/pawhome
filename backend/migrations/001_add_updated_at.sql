-- Migration 001 (Task 2): add an updated_at column to every table.
--
-- Why: incremental loading into the data lake needs a column that changes
-- whenever a row changes. created_at never changes and id only grows, so
-- neither can show that an existing row was edited. updated_at can.
--
-- Safe to run more than once: each step checks whether it was already done.

-- 1) Add the column. Only the FIRST time (when the column doesn't exist yet),
--    fill it with a realistic starting value: the row's own date.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'shelters' AND column_name = 'updated_at') THEN
    ALTER TABLE shelters ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();
    DROP TRIGGER IF EXISTS trg_shelters_updated_at ON shelters;  -- so it can't overwrite the backfill
    UPDATE shelters SET updated_at = created_at;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'adopters' AND column_name = 'updated_at') THEN
    ALTER TABLE adopters ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();
    DROP TRIGGER IF EXISTS trg_adopters_updated_at ON adopters;  -- so it can't overwrite the backfill
    UPDATE adopters SET updated_at = created_at;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'animals' AND column_name = 'updated_at') THEN
    ALTER TABLE animals ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();
    DROP TRIGGER IF EXISTS trg_animals_updated_at ON animals;  -- so it can't overwrite the backfill
    -- animals only have an arrival DATE; add the id as seconds so values differ
    UPDATE animals SET updated_at = arrived_at + make_interval(secs => id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'applications' AND column_name = 'updated_at') THEN
    ALTER TABLE applications ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();
    DROP TRIGGER IF EXISTS trg_applications_updated_at ON applications;  -- so it can't overwrite the backfill
    -- last change of an application = its decision, or its submission if still pending
    UPDATE applications SET updated_at = COALESCE(decided_at, submitted_at);
  END IF;
END $$;

-- 2) A trigger function: before any UPDATE, set updated_at to "now".
--    The database does this itself, so no backend code has to remember it.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3) Attach the function to each table.
DROP TRIGGER IF EXISTS trg_shelters_updated_at ON shelters;
CREATE TRIGGER trg_shelters_updated_at BEFORE UPDATE ON shelters
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_adopters_updated_at ON adopters;
CREATE TRIGGER trg_adopters_updated_at BEFORE UPDATE ON adopters
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_animals_updated_at ON animals;
CREATE TRIGGER trg_animals_updated_at BEFORE UPDATE ON animals
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_applications_updated_at ON applications;
CREATE TRIGGER trg_applications_updated_at BEFORE UPDATE ON applications
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 4) Indexes, because the incremental load asks "WHERE updated_at > last value".
CREATE INDEX IF NOT EXISTS idx_shelters_updated_at     ON shelters(updated_at);
CREATE INDEX IF NOT EXISTS idx_adopters_updated_at     ON adopters(updated_at);
CREATE INDEX IF NOT EXISTS idx_animals_updated_at      ON animals(updated_at);
CREATE INDEX IF NOT EXISTS idx_applications_updated_at ON applications(updated_at);