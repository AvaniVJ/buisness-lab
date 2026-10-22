import json, sqlite3
from pathlib import Path
from contextlib import contextmanager
from .config import settings

@contextmanager
def connect():
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(settings.database_path, timeout=30)
    conn.row_factory=sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS meetings(
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, meeting_label TEXT NOT NULL,
          transcript TEXT NOT NULL, analysis_json TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS baselines(
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, analysis_json TEXT NOT NULL,
          scope_json TEXT NOT NULL, estimate_json TEXT NOT NULL, proposal_json TEXT NOT NULL,
          approved INTEGER NOT NULL DEFAULT 0, reviewer TEXT, review_notes TEXT,
          created_at TEXT DEFAULT (datetime('now')));
        CREATE INDEX IF NOT EXISTS idx_baseline_project ON baselines(project_id,approved);
        """)

def save_meeting(project_id, label, transcript, analysis):
    with connect() as c:
        cur=c.execute("INSERT INTO meetings(project_id,meeting_label,transcript,analysis_json) VALUES(?,?,?,?)",
                      (project_id,label,transcript,json.dumps(analysis)))
        return cur.lastrowid

def save_baseline(project_id, analysis, scope, estimate, proposal):
    with connect() as c:
        cur=c.execute("""INSERT INTO baselines(project_id,analysis_json,scope_json,estimate_json,proposal_json)
          VALUES(?,?,?,?,?)""",(project_id,json.dumps(analysis),json.dumps(scope),json.dumps(estimate),json.dumps(proposal)))
        return cur.lastrowid

def get_baseline(baseline_id):
    with connect() as c:
        row=c.execute("SELECT * FROM baselines WHERE id=?",(baseline_id,)).fetchone()
        return dict(row) if row else None

def latest_approved_baseline(project_id):
    with connect() as c:
        row=c.execute("SELECT * FROM baselines WHERE project_id=? AND approved=1 ORDER BY id DESC LIMIT 1",(project_id,)).fetchone()
        return dict(row) if row else None

def review_baseline(baseline_id, reviewer, approved, notes):
    with connect() as c:
        cur=c.execute("UPDATE baselines SET approved=?,reviewer=?,review_notes=? WHERE id=?",
                      (1 if approved else 0,reviewer,notes,baseline_id))
        return cur.rowcount > 0

def list_baselines(project_id):
    with connect() as c:
        rows=c.execute("SELECT id,project_id,approved,reviewer,created_at FROM baselines WHERE project_id=? ORDER BY id DESC",(project_id,)).fetchall()
        return [dict(r) for r in rows]
