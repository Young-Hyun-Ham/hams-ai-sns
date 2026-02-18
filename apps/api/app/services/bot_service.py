import json

import psycopg

DEFAULT_JOB_INTERVAL_SECONDS = 300


def list_bots(conn: psycopg.Connection, user_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, name, persona, topic, is_active
            FROM bots
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,),
        )
        return list(cur.fetchall())


def create_bot(conn: psycopg.Connection, user_id: int, name: str, persona: str, topic: str) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bots (user_id, name, persona, topic)
            VALUES (%s, %s, %s, %s)
            RETURNING id, user_id, name, persona, topic, is_active
            """,
            (user_id, name, persona, topic),
        )
        bot = cur.fetchone()

        seed_jobs = [
            (bot["id"], "ai_create_post", json.dumps({"tone": "friendly"}), DEFAULT_JOB_INTERVAL_SECONDS),
            (
                bot["id"],
                "ai_create_comment",
                json.dumps({"tone": "supportive", "fallback": "좋은 인사이트 감사합니다!"}),
                DEFAULT_JOB_INTERVAL_SECONDS,
            ),
        ]
        cur.executemany(
            """
            INSERT INTO bot_jobs (bot_id, job_type, payload, interval_seconds)
            VALUES (%s, %s, %s::jsonb, %s)
            """,
            seed_jobs,
        )

    conn.commit()
    return bot


def update_bot(conn: psycopg.Connection, bot_id: int, user_id: int, payload: dict) -> dict | None:
    fields: list[str] = []
    values: list = []

    for key in ["name", "persona", "topic", "is_active"]:
        if payload.get(key) is not None:
            fields.append(f"{key} = %s")
            values.append(payload[key])

    if not fields:
        return get_bot(conn, bot_id, user_id)

    values.extend([bot_id, user_id])

    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE bots
            SET {', '.join(fields)}, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, name, persona, topic, is_active
            """,
            tuple(values),
        )
        bot = cur.fetchone()
    conn.commit()
    return bot


def delete_bot(conn: psycopg.Connection, bot_id: int, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM bots WHERE id = %s AND user_id = %s",
            (bot_id, user_id),
        )
        deleted = cur.rowcount > 0
    conn.commit()
    return deleted


def get_bot(conn: psycopg.Connection, bot_id: int, user_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, name, persona, topic, is_active
            FROM bots
            WHERE id = %s AND user_id = %s
            """,
            (bot_id, user_id),
        )
        return cur.fetchone()


def list_bot_jobs(conn: psycopg.Connection, bot_id: int, user_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT j.id, j.bot_id, j.job_type, j.payload, j.interval_seconds,
                   j.next_run_at, j.status, j.retry_count, j.max_retries, j.last_error
            FROM bot_jobs j
            INNER JOIN bots b ON b.id = j.bot_id
            WHERE j.bot_id = %s AND b.user_id = %s
            ORDER BY j.id DESC
            """,
            (bot_id, user_id),
        )
        return list(cur.fetchall())


def list_activity_logs(conn: psycopg.Connection, user_id: int, limit: int = 30) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT l.id, l.bot_id, l.job_id, l.job_type, l.result_status, l.message, l.executed_at
            FROM activity_logs l
            INNER JOIN bots b ON b.id = l.bot_id
            WHERE b.user_id = %s
            ORDER BY l.id DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return list(cur.fetchall())
