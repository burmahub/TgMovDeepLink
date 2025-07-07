import os
import sqlite3
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Get a database connection (SQLite for local, PostgreSQL for Railway)."""
    if DATABASE_URL:
        # Parse DATABASE_URL for PostgreSQL (Railway)
        conn = psycopg2.connect(DATABASE_URL)
    else:
        # Use SQLite locally
        conn = sqlite3.connect("videos.db")
    return conn

def init_db():
    """Initialize the database and create the videos table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create videos table (adapt for PostgreSQL or SQLite)
    if DATABASE_URL:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                chat_id BIGINT NOT NULL
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                chat_id INTEGER NOT NULL
            )
        """)
    
    conn.commit()
    cursor.close()
    conn.close()

def save_video(video_id: str, file_id: str, chat_id: int):
    """Save video metadata to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO videos (id, file_id, chat_id) VALUES (%s, %s, %s)",
        (video_id, file_id, chat_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_video(video_id: str):
    """Retrieve video metadata by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, chat_id FROM videos WHERE id = %s", (video_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result
