"""Transactional local history; no Home Assistant dependencies."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

PEOPLE = {"Maximilian", "Paul", "Vera", "Manuel"}
CHILDREN = {"Maximilian", "Paul"}
INVALID = {"unknown", "unavailable", ""}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, path):
        self.path = str(path)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def initialize(self):
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS cycles (
                id TEXT PRIMARY KEY, cycle_key TEXT UNIQUE,
                finished_at TEXT NOT NULL, assigned_to TEXT NOT NULL,
                status TEXT NOT NULL, emptied_at TEXT, emptied_by TEXT,
                observed_after_restart INTEGER NOT NULL DEFAULT 0,
                closed_at TEXT)""")

    @staticmethod
    def _insert(db, assigned_to, cycle_key=None, after_restart=False):
        if assigned_to not in CHILDREN:
            raise ValueError("Der Dienst-Helfer muss Maximilian oder Paul enthalten.")
        if cycle_key:
            existing = db.execute("SELECT * FROM cycles WHERE cycle_key=?", (cycle_key,)).fetchone()
            if existing:
                return dict(existing), False
        stamp = utcnow()
        # Household fallback for an unconfirmed previous load. This is an
        # assumed parent contribution, not a scan or a known emptying time.
        db.execute("""UPDATE cycles SET status='nicht_bestaetigt',
            emptied_by='Vera/Manuel', closed_at=? WHERE status='offen'""", (stamp,))
        record_id = uuid4().hex
        db.execute("""INSERT INTO cycles
            (id, cycle_key, finished_at, assigned_to, status, observed_after_restart)
            VALUES (?, ?, ?, ?, 'offen', ?)""",
            (record_id, cycle_key, stamp, assigned_to, int(after_restart)))
        return dict(db.execute("SELECT * FROM cycles WHERE id=?", (record_id,)).fetchone()), True

    def observe(self, state, assigned_to, startup=False):
        if state in INVALID:
            return None, False
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT value FROM metadata WHERE key='source_state'").fetchone()
            previous = previous['value'] if previous else None
            result = (None, False)
            # Initial installation while already finished is only a baseline:
            # we do not invent the historical finish time.
            if state == 'finished' and previous is not None and previous != 'finished':
                result = self._insert(db, assigned_to, after_restart=startup)
            db.execute("INSERT OR REPLACE INTO metadata (key,value) VALUES ('source_state',?)", (state,))
            return result

    def record_finished(self, assigned_to, cycle_key):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            return self._insert(db, assigned_to, cycle_key)

    def record_emptied(self, cycle_id, person):
        if person not in PEOPLE:
            raise ValueError('Unbekannte Person.')
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute('SELECT * FROM cycles WHERE id=?', (cycle_id,)).fetchone()
            if row is None:
                raise ValueError('Spülgang nicht gefunden.')
            if person in CHILDREN and person != row['assigned_to']:
                raise ValueError('Dieses Kind ist für den Spülgang nicht zuständig.')
            if row['status'] == 'erledigt':
                if row['emptied_by'] == person:
                    return dict(row), False
                raise ValueError('Dieser Spülgang wurde bereits bestätigt.')
            if row['status'] != 'offen':
                raise ValueError('Der Spülgang ist nicht mehr offen.')
            stamp = utcnow()
            db.execute("UPDATE cycles SET status='erledigt', emptied_at=?, emptied_by=?, closed_at=? WHERE id=?",
                       (stamp, person, stamp, cycle_id))
            return dict(db.execute('SELECT * FROM cycles WHERE id=?', (cycle_id,)).fetchone()), True

    def report(self, limit=30, offset=0):
        with self.connect() as db:
            rows = [dict(row) for row in db.execute(
                'SELECT * FROM cycles ORDER BY finished_at DESC, rowid DESC LIMIT ? OFFSET ?', (limit, offset))]
            for row in rows:
                row['observed_after_restart'] = bool(row['observed_after_restart'])
                row['waiting_minutes'] = None
                if row['emptied_at']:
                    row['waiting_minutes'] = round((datetime.fromisoformat(row['emptied_at']) -
                                                   datetime.fromisoformat(row['finished_at'])).total_seconds()/60, 1)
            return {
                'total': db.execute('SELECT COUNT(*) FROM cycles').fetchone()[0],
                'open_id': next((r['id'] for r in db.execute("SELECT id FROM cycles WHERE status='offen'")), None),
                'entries': rows,
            }
