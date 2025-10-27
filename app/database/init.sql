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

-- texts (публичный контент)
CREATE TABLE IF NOT EXISTS texts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page TEXT NOT NULL,
  key TEXT NOT NULL,
  lang TEXT NOT NULL,
  value TEXT NOT NULL,
  UNIQUE(page, key, lang)
);
CREATE INDEX IF NOT EXISTS idx_texts_page_lang ON texts(page, lang);

-- texts_crm (системные переводы CMS)
CREATE TABLE IF NOT EXISTS texts_crm (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page TEXT NOT NULL,
  key TEXT NOT NULL,
  lang TEXT NOT NULL,
  value TEXT NOT NULL,
  UNIQUE(page, key, lang)
);
CREATE INDEX IF NOT EXISTS idx_texts_crm_page_lang ON texts_crm(page, lang);

-- images
CREATE TABLE IF NOT EXISTS images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  original_path TEXT NOT NULL,
  type TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_images_type ON images(type);

-- images_alts - переводы для alt-тегов изображений
CREATE TABLE IF NOT EXISTS images_alts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_id INTEGER NOT NULL,
  lang TEXT NOT NULL,
  alt_text TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
  UNIQUE(image_id, lang)
);
CREATE INDEX IF NOT EXISTS idx_images_alts_image_id ON images_alts(image_id);
CREATE INDEX IF NOT EXISTS idx_images_alts_lang ON images_alts(lang);

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