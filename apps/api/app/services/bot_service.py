import json

import psycopg

DEFAULT_JOB_INTERVAL_SECONDS = 300


def _validate_ai_config(ai_provider: str, api_key: str, ai_model: str) -> None:
    provider = (ai_provider or "").strip().lower()
    if provider not in {"mock", "gpt", "gemini", "claude"}:
        raise ValueError("지원하지 않는 AI 종류입니다.")

    if provider == "mock":
        return

    if not api_key.strip():
        raise ValueError("API Key를 입력해주세요.")
    if not ai_model.strip():
        raise ValueError("모델을 선택해주세요.")


def list_bots(conn: psycopg.Connection, user_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id,
                   user_id,
                   name,
                   persona,
                   topic,
                   ai_provider,
                   ai_model,
                   (api_key IS NOT NULL AND api_key <> '') AS has_api_key,
                   is_active
            FROM bots
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,),
        )
        return list(cur.fetchall())


def create_bot(
    conn: psycopg.Connection,
    user_id: int,
    name: str,
    persona: str,
    topic: str,
    ai_provider: str,
    api_key: str,
    ai_model: str,
) -> dict:
    _validate_ai_config(ai_provider, api_key, ai_model)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bots (user_id, name, persona, topic, ai_provider, api_key, ai_model)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id,
                      user_id,
                      name,
                      persona,
                      topic,
                      ai_provider,
                      ai_model,
                      (api_key IS NOT NULL AND api_key <> '') AS has_api_key,
                      is_active
            """,
            (user_id, name, persona, topic, ai_provider, api_key.strip(), ai_model),
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

    for key in ["name", "persona", "topic", "is_active", "ai_provider", "api_key", "ai_model"]:
        if payload.get(key) is not None:
            fields.append(f"{key} = %s")
            value = payload[key].strip() if key == "api_key" and isinstance(payload[key], str) else payload[key]
            values.append(value)

    if not fields:
        return get_bot(conn, bot_id, user_id)

    if any(payload.get(k) is not None for k in ["ai_provider", "api_key", "ai_model"]):
        current = _get_bot_internal(conn, bot_id, user_id)
        if not current:
            return None
        _validate_ai_config(
            payload.get("ai_provider") or current["ai_provider"],
            payload.get("api_key") if payload.get("api_key") is not None else (current.get("api_key") or ""),
            payload.get("ai_model") or current["ai_model"],
        )

    values.extend([bot_id, user_id])

    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE bots
            SET {', '.join(fields)}, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id,
                      user_id,
                      name,
                      persona,
                      topic,
                      ai_provider,
                      ai_model,
                      (api_key IS NOT NULL AND api_key <> '') AS has_api_key,
                      is_active
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


def _get_bot_internal(conn: psycopg.Connection, bot_id: int, user_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id,
                   user_id,
                   name,
                   persona,
                   topic,
                   ai_provider,
                   api_key,
                   ai_model,
                   is_active
            FROM bots
            WHERE id = %s AND user_id = %s
            """,
            (bot_id, user_id),
        )
        return cur.fetchone()


def get_bot(conn: psycopg.Connection, bot_id: int, user_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id,
                   user_id,
                   name,
                   persona,
                   topic,
                   ai_provider,
                   ai_model,
                   (api_key IS NOT NULL AND api_key <> '') AS has_api_key,
                   is_active
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
