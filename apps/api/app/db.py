import os
from collections.abc import Generator

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hams:hams@localhost:5432/hams")


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def get_db() -> Generator[psycopg.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    nickname VARCHAR(100) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS bots (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    persona TEXT NOT NULL,
                    topic VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_jobs (
                    id BIGSERIAL PRIMARY KEY,
                    bot_id BIGINT NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
                    job_type VARCHAR(50) NOT NULL,
                    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                    interval_seconds INT NOT NULL DEFAULT 300,
                    next_run_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    retry_count INT NOT NULL DEFAULT 0,
                    max_retries INT NOT NULL DEFAULT 3,
                    last_error TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bot_jobs_scheduler
                ON bot_jobs (status, next_run_at);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sns_posts (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    bot_id BIGINT REFERENCES bots(id) ON DELETE SET NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    is_anonymous BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sns_posts_user_created
                ON sns_posts (user_id, created_at DESC);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id BIGSERIAL PRIMARY KEY,
                    bot_id BIGINT NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
                    job_id BIGINT NOT NULL REFERENCES bot_jobs(id) ON DELETE CASCADE,
                    job_type VARCHAR(50) NOT NULL,
                    result_status VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
        conn.commit()
