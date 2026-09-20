-- Brand DNA Stage 3–4 (apply manually in Supabase).
-- ID types must match live users.id and brand_profiles.id (uuid vs text).
--
-- Voice stack: Pipecat sidecar (optional) uses interview_sessions via FastAPI;
-- see ai-social-media-ui/docs/BRAND_DNA_VOICE_STACK.md

CREATE TABLE IF NOT EXISTS interview_sessions (

    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,

    brand_profile_id uuid NOT NULL REFERENCES brand_profiles (id) ON DELETE CASCADE,

    status text NOT NULL DEFAULT 'in_progress',

    prep_brief text NOT NULL DEFAULT '',

    questions jsonb NOT NULL DEFAULT '[]'::jsonb,

    transcript text NOT NULL DEFAULT '',

    follow_up_used boolean NOT NULL DEFAULT false,

    created_at timestamptz NOT NULL DEFAULT now(),

    updated_at timestamptz NOT NULL DEFAULT now(),

    completed_at timestamptz

);


CREATE TABLE IF NOT EXISTS brand_voice_studies (

    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,

    brand_profile_id uuid NOT NULL REFERENCES brand_profiles (id) ON DELETE CASCADE,

    keep_items jsonb NOT NULL DEFAULT '[]'::jsonb,

    raise_items jsonb NOT NULL DEFAULT '[]'::jsonb,

    source_summary text NOT NULL DEFAULT '',

    created_at timestamptz NOT NULL DEFAULT now()

);


CREATE TABLE IF NOT EXISTS brand_channel_preferences (

    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,

    brand_profile_id uuid NOT NULL REFERENCES brand_profiles (id) ON DELETE CASCADE,

    platform text NOT NULL,

    tone_notes text NOT NULL DEFAULT '',

    length_notes text NOT NULL DEFAULT '',

    hashtag_notes text NOT NULL DEFAULT '',

    created_at timestamptz NOT NULL DEFAULT now(),

    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (brand_profile_id, platform)

);
