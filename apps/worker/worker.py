import json
import os
import time
from datetime import UTC, datetime

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hams:hams@localhost:5432/hams")
WORKER_POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "10"))
WORKER_BATCH_SIZE = int(os.getenv("WORKER_BATCH_SIZE", "10"))
WORKER_RETRY_DELAY_SECONDS = int(os.getenv("WORKER_RETRY_DELAY_SECONDS", "30"))


class WorkerError(Exception):
    pass


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def claim_due_jobs(conn: psycopg.Connection, batch_size: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH claim AS (
                SELECT j.id
                FROM bot_jobs j
                INNER JOIN bots b ON b.id = j.bot_id
                WHERE j.status = 'active'
                  AND b.is_active = TRUE
                  AND j.next_run_at <= NOW()
                ORDER BY j.next_run_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT %s
            )
            UPDATE bot_jobs j
            SET updated_at = NOW()
            FROM claim
            WHERE j.id = claim.id
            RETURNING j.id, j.bot_id, j.job_type, j.payload, j.interval_seconds,
                      j.retry_count, j.max_retries;
            """,
            (batch_size,),
        )
        return list(cur.fetchall())


def execute_job(conn: psycopg.Connection, job: dict) -> None:
    bot = get_bot(conn, job["bot_id"])
    if not bot:
        raise WorkerError(f"bot({job['bot_id']}) not found")

    if job["job_type"] == "post_text":
        message = run_post_text(bot, job["payload"])
    elif job["job_type"] == "follow_user":
        message = run_follow_user(bot, job["payload"])
    else:
        raise WorkerError(f"unsupported job_type: {job['job_type']}")

    insert_activity_log(conn, job, "success", message)
    mark_job_success(conn, job)


def get_bot(conn: psycopg.Connection, bot_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, persona, topic FROM bots WHERE id = %s", (bot_id,))
        return cur.fetchone()


def run_post_text(bot: dict, payload: dict | str) -> str:
    if isinstance(payload, str):
        payload = json.loads(payload)
    tone = payload.get("tone", "neutral")
    return f"[{tone}] {bot['name']}({bot['persona']})가 '{bot['topic']}' 주제로 게시글을 발행했습니다."


def run_follow_user(bot: dict, payload: dict | str) -> str:
    if isinstance(payload, str):
        payload = json.loads(payload)
    target = payload.get("target", "new_user")
    return f"{bot['name']} 봇이 @{target} 계정을 팔로우했습니다."


def insert_activity_log(conn: psycopg.Connection, job: dict, status: str, message: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO activity_logs (bot_id, job_id, job_type, result_status, message)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (job["bot_id"], job["id"], job["job_type"], status, message),
        )


def mark_job_success(conn: psycopg.Connection, job: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE bot_jobs
            SET retry_count = 0,
                last_error = NULL,
                next_run_at = NOW() + (interval_seconds * INTERVAL '1 second'),
                updated_at = NOW()
            WHERE id = %s
            """,
            (job["id"],),
        )


def mark_job_failure(conn: psycopg.Connection, job: dict, error_message: str) -> None:
    should_pause = (job["retry_count"] + 1) >= job["max_retries"]

    with conn.cursor() as cur:
        if should_pause:
            cur.execute(
                """
                UPDATE bot_jobs
                SET status = 'paused',
                    retry_count = retry_count + 1,
                    last_error = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (error_message, job["id"]),
            )
        else:
            cur.execute(
                """
                UPDATE bot_jobs
                SET retry_count = retry_count + 1,
                    last_error = %s,
                    next_run_at = NOW() + (%s * INTERVAL '1 second'),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (error_message, WORKER_RETRY_DELAY_SECONDS, job["id"]),
            )

    insert_activity_log(conn, job, "failed", error_message)


def process_once() -> int:
    processed = 0
    with get_connection() as conn:
        with conn.transaction():
            jobs = claim_due_jobs(conn, WORKER_BATCH_SIZE)

        for job in jobs:
            try:
                with conn.transaction():
                    execute_job(conn, job)
                processed += 1
            except Exception as exc:  # noqa: BLE001
                with conn.transaction():
                    mark_job_failure(conn, job, str(exc))
                print(f"[worker] job failed id={job['id']} error={exc}", flush=True)

    return processed


def main() -> None:
    print(
        f"[{datetime.now(UTC).isoformat()}] worker started poll={WORKER_POLL_SECONDS}s batch={WORKER_BATCH_SIZE}",
        flush=True,
    )
    while True:
        count = process_once()
        print(f"[{datetime.now(UTC).isoformat()}] processed_jobs={count}", flush=True)
        time.sleep(WORKER_POLL_SECONDS)


if __name__ == "__main__":
    main()
