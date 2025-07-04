import psycopg2
import os
from datetime import datetime

DATABASE_URL = os.environ["DATABASE_URL"]

with psycopg2.connect(DATABASE_URL, sslmode="require") as con:
    with con.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                payload_id BIGINT PRIMARY KEY,
                file_id TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS access_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                payload_id BIGINT NOT NULL,
                accessed_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        # Example insert
        cur.execute(
            "INSERT INTO videos (payload_id, file_id, created_at) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (4000053548, "BAACAgUAAxkBAA...", datetime.utcnow()),
        )
    con.commit()
print("Sample data inserted.")