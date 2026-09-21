-- Corpus clean break: single append-only source of truth for generation.
-- Apply manually in Supabase after brand_dna_stage1_2.sql.
-- ID types must match live users.id and brand_profiles.id.

CREATE TABLE IF NOT EXISTS corpus_items (

    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,

    brand_profile_id uuid NOT NULL REFERENCES brand_profiles (id) ON DELETE CASCADE,

    content text NOT NULL,

    source text NOT NULL,

    theme text,

    question_text text NOT NULL DEFAULT '',

    session_id uuid,

    created_at timestamptz NOT NULL DEFAULT now()

);

CREATE INDEX IF NOT EXISTS corpus_items_brand_created_idx
    ON corpus_items (brand_profile_id, created_at DESC);

CREATE INDEX IF NOT EXISTS corpus_items_user_brand_idx
    ON corpus_items (user_id, brand_profile_id);

-- Optional: persist talk mode on sessions (mini vs full).
ALTER TABLE interview_sessions
ADD COLUMN IF NOT EXISTS capture_mode text NOT NULL DEFAULT 'full';
