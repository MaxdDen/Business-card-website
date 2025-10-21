-- Idempotent schema initialization
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- users
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('admin','editor')),
  created_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- texts
CREATE TABLE IF NOT EXISTS texts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page TEXT NOT NULL,
  key TEXT NOT NULL,
  lang TEXT NOT NULL,
  value TEXT NOT NULL,
  UNIQUE(page, key, lang)
);
CREATE INDEX IF NOT EXISTS idx_texts_page_lang ON texts(page, lang);

-- images
CREATE TABLE IF NOT EXISTS images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  original_path TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('logo','slider','background','favicon')),
  "order" INTEGER NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_images_type ON images(type);

-- seo
CREATE TABLE IF NOT EXISTS seo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page TEXT NOT NULL,
  lang TEXT NOT NULL,
  title TEXT,
  description TEXT,
  keywords TEXT,
  UNIQUE(page, lang)
);


