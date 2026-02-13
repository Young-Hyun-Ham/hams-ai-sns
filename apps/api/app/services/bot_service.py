import psycopg


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
