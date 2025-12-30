ALTER TABLE job_batches
ADD COLUMN IF NOT EXISTS last_heartbeat_at timestamptz;
