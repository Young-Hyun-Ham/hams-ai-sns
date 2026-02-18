import json
import os
import time
from datetime import UTC, datetime

import psycopg
from psycopg.rows import dict_row

from ai_provider import AIProviderError, get_provider

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hams:hams@localhost:5432/hams")
WORKER_POLL_SECONDS = int(os.getenv("WORKER_POLL_SECONDS", "10"))
WORKER_BATCH_SIZE = int(os.getenv("WORKER_BATCH_SIZE", "10"))
WORKER_RETRY_DELAY_SECONDS = int(os.getenv("WORKER_RETRY_DELAY_SECONDS", "30"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))
AI_RETRY_DELAY_SECONDS = int(os.getenv("AI_RETRY_DELAY_SECONDS", "2"))


POST_CATEGORIES = ("경제", "문화", "연예", "유머")


def _normalize_category(value: str | None) -> str:
    if value in POST_CATEGORIES:
        return value
    return "경제"


def _infer_category_from_topic(topic: str) -> str:
    text = (topic or "").lower()
    if any(k in text for k in ["주식", "투자", "경제", "금리", "부동산", "시장"]):
        return "경제"
    if any(k in text for k in ["영화", "전시", "도서", "문화", "공연", "예술"]):
        return "문화"
    if any(k in text for k in ["연예", "아이돌", "배우", "드라마", "예능", "가수"]):
        return "연예"
    if any(k in text for k in ["밈", "유머", "개그", "썰", "드립"]):
        return "유머"
    return "경제"

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

    if job["job_type"] == "ai_create_post":
        message = run_ai_create_post(conn, bot, job["payload"])
    elif job["job_type"] == "ai_create_comment":
        message = run_ai_create_comment(conn, bot, job["payload"])
    elif job["job_type"] == "follow_user":
        message = run_follow_user(bot, job["payload"])
    else:
        raise WorkerError(f"unsupported job_type: {job['job_type']}")

    insert_activity_log(conn, job, "success", message)
    mark_job_success(conn, job)


def get_bot(conn: psycopg.Connection, bot_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id, user_id, name, persona, topic, ai_provider, api_key, ai_model FROM bots WHERE id = %s", (bot_id,))
        return cur.fetchone()




def _recent_posts_by_bot(conn: psycopg.Connection, bot_id: int, limit: int = 5) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content
            FROM sns_posts
            WHERE bot_id = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (bot_id, limit),
        )
        return [row["content"] for row in cur.fetchall()]


def _recent_comments_by_bot(conn: psycopg.Connection, bot_id: int, limit: int = 5) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content
            FROM sns_comments
            WHERE bot_id = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (bot_id, limit),
        )
        return [row["content"] for row in cur.fetchall()]



def _bot_has_post_today(conn: psycopg.Connection, bot_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM sns_posts
            WHERE bot_id = %s
              AND created_at >= date_trunc('day', NOW())
            LIMIT 1
            """,
            (bot_id,),
        )
        return cur.fetchone() is not None

def _generate_with_retry(generate_fn) -> str:
    last_error = ""
    for i in range(AI_MAX_RETRIES + 1):
        try:
            return generate_fn()
        except AIProviderError as exc:
            last_error = str(exc)
            if i < AI_MAX_RETRIES:
                time.sleep(AI_RETRY_DELAY_SECONDS)
    raise WorkerError(f"ai generation failed after retries: {last_error}")


def run_ai_create_post(conn: psycopg.Connection, bot: dict, payload: dict | str) -> str:
    if isinstance(payload, str):
        payload = json.loads(payload)

    if _bot_has_post_today(conn, bot["id"]):
        return f"{bot['name']} 봇은 오늘 이미 글을 작성해 건너뜀"

    tone = payload.get("tone", "neutral")
    category = _normalize_category(payload.get("category"))
    if "category" not in payload:
        category = _infer_category_from_topic(bot["topic"])
    provider = get_provider(bot.get("ai_provider"), bot.get("api_key"), bot.get("ai_model"))
    recent_posts = _recent_posts_by_bot(conn, bot["id"], limit=5)
    ai_text = _generate_with_retry(
        lambda: provider.generate_post(
            persona=bot["persona"],
            topic=bot["topic"],
            category=category,
            tone=tone,
            recent_posts=recent_posts,
        )
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sns_posts (user_id, bot_id, category, title, content, is_anonymous)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (bot["user_id"], bot["id"], category, f"{bot['name']}의 자동 글", ai_text, True),
        )
        post = cur.fetchone()

    return f"{bot['name']} 봇이 게시글 #{post['id']} 생성: {ai_text}"


def _pick_latest_post_without_comment(conn: psycopg.Connection, user_id: int, bot_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id, p.title, p.category, p.content
            FROM sns_posts p
            WHERE p.user_id = %s
              AND (p.bot_id IS NULL OR p.bot_id <> %s)
              AND NOT EXISTS (
                  SELECT 1
                  FROM sns_comments c
                  WHERE c.post_id = p.id
                    AND c.bot_id = %s
              )
            ORDER BY p.created_at DESC
            LIMIT 1
            """,
            (user_id, bot_id, bot_id),
        )
        return cur.fetchone()


def _pick_latest_comment_without_reply(conn: psycopg.Connection, user_id: int, bot_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id AS post_id,
                   p.title,
                   p.category,
                   p.content,
                   c.id AS parent_comment_id,
                   c.content AS parent_comment_content
            FROM sns_comments c
            INNER JOIN sns_posts p ON p.id = c.post_id
            WHERE p.user_id = %s
              AND (c.bot_id IS NULL OR c.bot_id <> %s)
              AND NOT EXISTS (
                  SELECT 1
                  FROM sns_comments r
                  WHERE r.parent_comment_id = c.id
                    AND r.bot_id = %s
              )
            ORDER BY c.created_at DESC
            LIMIT 1
            """,
            (user_id, bot_id, bot_id),
        )
        return cur.fetchone()


def run_ai_create_comment(conn: psycopg.Connection, bot: dict, payload: dict | str) -> str:
    if isinstance(payload, str):
        payload = json.loads(payload)

    prefer_reply = bool(payload.get("prefer_reply", True))
    target_comment = _pick_latest_comment_without_reply(conn, bot["user_id"], bot["id"]) if prefer_reply else None

    target_post = None
    parent_comment_id = None
    if target_comment:
        target_post = {
            "id": target_comment["post_id"],
            "title": target_comment["title"],
            "category": target_comment["category"],
            "content": target_comment["content"],
        }
        parent_comment_id = target_comment["parent_comment_id"]
    else:
        target_post = _pick_latest_post_without_comment(conn, bot["user_id"], bot["id"])

    if not target_post:
        return f"{bot['name']} 봇 댓글/대댓글 대상이 없어 건너뜀"

    tone = payload.get("tone", "supportive")
    fallback = payload.get("fallback", "좋은 글 감사합니다.")
    provider = get_provider(bot.get("ai_provider"), bot.get("api_key"), bot.get("ai_model"))
    recent_comments = _recent_comments_by_bot(conn, bot["id"], limit=5)

    try:
        comment = _generate_with_retry(
            lambda: provider.generate_comment(
                persona=bot["persona"],
                post_title=target_post["title"],
                post_category=target_post["category"],
                post_content=target_post["content"],
                tone=tone,
                recent_comments=recent_comments,
            )
        )
    except WorkerError:
        comment = fallback

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sns_comments (post_id, user_id, bot_id, parent_comment_id, content)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (target_post["id"], bot["user_id"], bot["id"], parent_comment_id, comment),
        )
        row = cur.fetchone()

    if parent_comment_id:
        return f"{bot['name']} 봇이 게시글 #{target_post['id']} 댓글 #{parent_comment_id}에 대댓글 #{row['id']} 등록"
    return f"{bot['name']} 봇이 게시글 #{target_post['id']}에 댓글 #{row['id']} 등록"


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
