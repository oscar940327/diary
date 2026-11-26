CREATE TABLE entries (
  id TEXT PRIMARY KEY NOT NULL,
  application_id TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  guild_id TEXT NOT NULL,
  submission_id TEXT NOT NULL,
  original_content TEXT NOT NULL,
  requested_date TEXT,
  entry_date TEXT NOT NULL,
  created_at TEXT NOT NULL,
  display_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (display_status IN ('pending', 'sent', 'uncertain')),
  display_lock_id TEXT,
  display_lock_expires_at_ms INTEGER,
  CHECK ((display_lock_id IS NULL) = (display_lock_expires_at_ms IS NULL)),
  UNIQUE (application_id, owner_id, guild_id, submission_id)
) STRICT;

CREATE TABLE entry_messages (
  entry_id TEXT NOT NULL REFERENCES entries (id),
  position INTEGER NOT NULL CHECK (position >= 1),
  content TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'sent', 'uncertain')),
  channel_id TEXT,
  message_id TEXT,
  failure_code TEXT,
  nonce TEXT NOT NULL,
  CHECK (status <> 'sent' OR (channel_id IS NOT NULL AND message_id IS NOT NULL)),
  PRIMARY KEY (entry_id, position)
) STRICT;
