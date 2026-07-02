import sqlite3
from pathlib import Path


DB_PATH = Path("users.db")


def create_database() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              user_id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              membership_tier TEXT NOT NULL
            );
            """
        )
        cursor.executemany(
            """
            INSERT OR REPLACE INTO users (user_id, name, membership_tier)
            VALUES (?, ?, ?);
            """,
            [
                (101, "Riya Sharma", "Gold"),
                (102, "Aman Verma", "Silver"),
                (103, "Neha Iyer", "Platinum"),
            ],
        )
        conn.commit()


if __name__ == "__main__":
    create_database()
    print(f"Created and seeded {DB_PATH}")
