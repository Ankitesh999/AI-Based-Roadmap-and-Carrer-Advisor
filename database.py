import sqlite3

def init_db(db_path='data/career_advisor.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Users table (updated)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        education TEXT NOT NULL,
        experience TEXT NOT NULL,
        goal TEXT NOT NULL,
        hours_per_week INTEGER NOT NULL,
        selected_career TEXT
    )''')
    # Migration: Add selected_career column if missing
    c.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in c.fetchall()]
    if 'selected_career' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN selected_career TEXT')
        conn.commit()
    # Roadmap tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS roadmap_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        phase TEXT NOT NULL,
        task TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Pending', 'In Progress', 'Completed')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    # Quiz scores table
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_scores (
        user_id INTEGER,
        analytical REAL,
        creativity REAL,
        engineering REAL,
        communication REAL,
        curiosity REAL,
        career_track TEXT,
        skill_name TEXT,
        user_level REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
