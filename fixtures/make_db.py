import os
import sqlite3

DB = os.path.join(os.path.dirname(__file__), "sample.db")
if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.executescript("""
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
""")
users = [
    (1, "Alice", "2024-01-05"),
    (2, "Bob", "2024-01-10"),
    (3, "Carol", "2024-02-01"),
    (4, "Dave", "2024-02-15"),
]
orders = [
    (1, 1, 12.5, "2024-01-06"),
    (2, 1, 7.0, "2024-01-07"),
    (3, 2, 99.0, "2024-01-11"),
    (4, 3, 5.0, "2024-02-02"),
]
cur.executemany("INSERT INTO users VALUES (?,?,?)", users)
cur.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)
conn.commit()
conn.close()
print("created", DB)
