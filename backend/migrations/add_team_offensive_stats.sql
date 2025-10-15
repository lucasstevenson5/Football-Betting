-- Add offensive stats columns to team_stats table
-- Run this directly on PostgreSQL if migration script fails

-- Add columns if they don't exist
DO $$
BEGIN
    -- Add points_scored column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='team_stats' AND column_name='points_scored') THEN
        ALTER TABLE team_stats ADD COLUMN points_scored INTEGER DEFAULT 0;
        RAISE NOTICE 'Added points_scored column';
    END IF;

    -- Add total_yards column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='team_stats' AND column_name='total_yards') THEN
        ALTER TABLE team_stats ADD COLUMN total_yards INTEGER DEFAULT 0;
        RAISE NOTICE 'Added total_yards column';
    END IF;

    -- Add passing_yards column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='team_stats' AND column_name='passing_yards') THEN
        ALTER TABLE team_stats ADD COLUMN passing_yards INTEGER DEFAULT 0;
        RAISE NOTICE 'Added passing_yards column';
    END IF;

    -- Add rushing_yards column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='team_stats' AND column_name='rushing_yards') THEN
        ALTER TABLE team_stats ADD COLUMN rushing_yards INTEGER DEFAULT 0;
        RAISE NOTICE 'Added rushing_yards column';
    END IF;
END $$;
