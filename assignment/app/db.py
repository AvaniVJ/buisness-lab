import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import settings

def _ensure_parent():
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)

@contextmanager
def connect():
    _ensure_parent()
    conn = sqlite3.connect(settings.database_path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            last_modified TEXT,
            fetched_at TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_url TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            heading TEXT,
            text TEXT NOT NULL,
            embedding_json TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            UNIQUE(article_url, chunk_index),
            FOREIGN KEY(article_url) REFERENCES articles(url)
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_active ON chunks(active);
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            discovered INTEGER DEFAULT 0,
            added INTEGER DEFAULT 0,
            updated INTEGER DEFAULT 0,
            removed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            details_json TEXT
        );
        CREATE TABLE IF NOT EXISTS ingestion_manifest (
            url TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            expert_answer TEXT,
            reviewer TEXT,
            source_url TEXT
        );
        CREATE TABLE IF NOT EXISTS expert_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            source_url TEXT,
            reviewer TEXT NOT NULL,
            created_at TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        """)

def get_article(url: str):
    with connect() as conn:
        return conn.execute("SELECT * FROM articles WHERE url=?", (url,)).fetchone()

def active_urls():
    with connect() as conn:
        return {r["url"] for r in conn.execute("SELECT url FROM articles WHERE active=1")}

def save_article(url, title, content, content_hash, last_modified, fetched_at):
    with connect() as conn:
        conn.execute("""
        INSERT INTO articles(url,title,content,content_hash,last_modified,fetched_at,active)
        VALUES(?,?,?,?,?,?,1)
        ON CONFLICT(url) DO UPDATE SET title=excluded.title, content=excluded.content,
        content_hash=excluded.content_hash,last_modified=excluded.last_modified,
        fetched_at=excluded.fetched_at,active=1
        """, (url,title,content,content_hash,last_modified,fetched_at))

def replace_chunks(url, chunks):
    with connect() as conn:
        conn.execute("DELETE FROM chunks WHERE article_url=?", (url,))
        conn.executemany("""
        INSERT INTO chunks(article_url,chunk_index,heading,text,embedding_json,active)
        VALUES(?,?,?,?,?,1)
        """, [(url, i, c["heading"], c["text"], json.dumps(c.get("embedding"))) for i,c in enumerate(chunks)])

def mark_removed(urls):
    with connect() as conn:
        for url in urls:
            conn.execute("UPDATE articles SET active=0 WHERE url=?", (url,))
            conn.execute("UPDATE chunks SET active=0 WHERE article_url=?", (url,))
            conn.execute("UPDATE ingestion_manifest SET status='removed', updated_at=datetime('now') WHERE url=?", (url,))

def manifest_update(url, status, attempts=0, error=None):
    with connect() as conn:
        conn.execute("""
        INSERT INTO ingestion_manifest(url,status,attempts,last_error,updated_at) VALUES(?,?,?,?,datetime('now'))
        ON CONFLICT(url) DO UPDATE SET status=excluded.status, attempts=excluded.attempts,
        last_error=excluded.last_error, updated_at=excluded.updated_at
        """, (url,status,attempts,error))

def add_escalation(question, reason):
    with connect() as conn:
        cur = conn.execute("INSERT INTO escalations(question,reason,created_at,status) VALUES(?,?,datetime('now'),'open')",
                           (question,reason))
        return cur.lastrowid

def resolve_escalation(escalation_id, answer, reviewer, source_url):
    with connect() as conn:
        row = conn.execute("SELECT * FROM escalations WHERE id=?", (escalation_id,)).fetchone()
        if not row:
            return False
        conn.execute("UPDATE escalations SET status='resolved',expert_answer=?,reviewer=?,source_url=? WHERE id=?",
                     (answer,reviewer,source_url,escalation_id))
        conn.execute("""INSERT INTO expert_knowledge(question,answer,source_url,reviewer,created_at)
                     VALUES(?,?,?,?,datetime('now'))""", (row["question"],answer,source_url,reviewer))
        return True

def all_active_chunks():
    with connect() as conn:
        return conn.execute("""
        SELECT c.id,c.article_url,c.heading,c.text,c.embedding_json,a.title
        FROM chunks c JOIN articles a ON a.url=c.article_url
        WHERE c.active=1 AND a.active=1
        """).fetchall()

def active_expert_knowledge():
    with connect() as conn:
        return conn.execute("SELECT * FROM expert_knowledge WHERE active=1").fetchall()

def run_start():
    with connect() as conn:
        cur=conn.execute("INSERT INTO ingestion_runs(started_at,status) VALUES(datetime('now'),'running')")
        return cur.lastrowid

def run_finish(run_id, **values):
    with connect() as conn:
        conn.execute("""UPDATE ingestion_runs SET finished_at=datetime('now'),status=?,
        discovered=?,added=?,updated=?,removed=?,failed=?,details_json=? WHERE id=?""",
        (values.get("status","completed"),values.get("discovered",0),values.get("added",0),
         values.get("updated",0),values.get("removed",0),values.get("failed",0),
         json.dumps(values.get("details",{})),run_id))

def run_status():
    with connect() as conn:
        runs=conn.execute("SELECT * FROM ingestion_runs ORDER BY id DESC LIMIT 10").fetchall()
        manifest=conn.execute("SELECT status,COUNT(*) AS n FROM ingestion_manifest GROUP BY status").fetchall()
        return {"recent_runs":[dict(x) for x in runs], "manifest_counts":{x["status"]:x["n"] for x in manifest}}
