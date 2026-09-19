-- Brand DNA Stage 1+2 (apply manually in Supabase; no Alembic).
--
-- ID types: this repo has no live schema. Python models use string ids.
-- Columns below use uuid, matching typical Supabase public.users / brand_profiles.
-- They MUST match live brand_profiles.id and users.id (and existing FKs).
-- If those columns are text, change these uuid references to text before applying.
--
-- Canonical interview question_key values (client-supplied; API does not invent):
--   customers_get_wrong
--   changed_my_mind
--   unpublished_advice
--   customer_sentence
--   industry_disagree

ALTER TABLE brand_profiles
ADD COLUMN IF NOT EXISTS not_for text DEFAULT '';

ALTER TABLE brand_profiles
ADD COLUMN IF NOT EXISTS desired_outcome text DEFAULT '';


CREATE TABLE IF NOT EXISTS voice_samples (

    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,

    brand_profile_id uuid NOT NULL REFERENCES brand_profiles (id) ON DELETE CASCADE,

    source text NOT NULL,

    content text NOT NULL,

    created_at timestamptz NOT NULL DEFAULT now()

);


CREATE TABLE IF NOT EXISTS interview_answers (

    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,

    brand_profile_id uuid NOT NULL REFERENCES brand_profiles (id) ON DELETE CASCADE,

    question_key text NOT NULL,

    question_text text NOT NULL DEFAULT '',

    answer_text text NOT NULL DEFAULT '',

    source text NOT NULL,

    created_at timestamptz NOT NULL DEFAULT now(),

    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (brand_profile_id, question_key)

);
