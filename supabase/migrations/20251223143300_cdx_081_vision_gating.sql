-- CDX-081: Vision Gating + Two-Stage Vision Columns

ALTER TABLE public.threads_posts
    ADD COLUMN IF NOT EXISTS vision_mode text DEFAULT 'auto',
    ADD COLUMN IF NOT EXISTS vision_need_score numeric,
    ADD COLUMN IF NOT EXISTS vision_reasons jsonb,
    ADD COLUMN IF NOT EXISTS vision_stage_ran text DEFAULT 'none', -- none|v1|v2
    ADD COLUMN IF NOT EXISTS vision_v1 jsonb,
    ADD COLUMN IF NOT EXISTS vision_v2 jsonb,
    ADD COLUMN IF NOT EXISTS vision_sim_post_comments numeric,
    ADD COLUMN IF NOT EXISTS vision_metrics_reliable boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS vision_updated_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_threads_posts_vision_stage_ran
    ON public.threads_posts(vision_stage_ran);

CREATE INDEX IF NOT EXISTS idx_threads_posts_vision_updated_at
    ON public.threads_posts(vision_updated_at DESC);
