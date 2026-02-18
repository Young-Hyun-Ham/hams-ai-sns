import psycopg


def list_posts(conn: psycopg.Connection, user_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id,
                   p.user_id,
                   p.bot_id,
                   p.title,
                   p.content,
                   p.is_anonymous,
                   p.created_at,
                   p.updated_at,
                   b.name AS bot_name
            FROM sns_posts p
            LEFT JOIN bots b ON b.id = p.bot_id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()


def get_post(conn: psycopg.Connection, post_id: int, user_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id,
                   p.user_id,
                   p.bot_id,
                   p.title,
                   p.content,
                   p.is_anonymous,
                   p.created_at,
                   p.updated_at,
                   b.name AS bot_name
            FROM sns_posts p
            LEFT JOIN bots b ON b.id = p.bot_id
            WHERE p.id = %s AND p.user_id = %s
            """,
            (post_id, user_id),
        )
        return cur.fetchone()


def create_post(
    conn: psycopg.Connection,
    user_id: int,
    title: str,
    content: str,
    is_anonymous: bool,
    bot_id: int | None,
) -> dict:
    with conn.cursor() as cur:
        if bot_id is not None:
            cur.execute("SELECT id FROM bots WHERE id = %s AND user_id = %s", (bot_id, user_id))
            if not cur.fetchone():
                raise ValueError("유효하지 않은 봇입니다.")

        cur.execute(
            """
            INSERT INTO sns_posts (user_id, bot_id, title, content, is_anonymous)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id,
                      user_id,
                      bot_id,
                      title,
                      content,
                      is_anonymous,
                      created_at,
                      updated_at
            """,
            (user_id, bot_id, title, content, is_anonymous),
        )
        row = cur.fetchone()
        conn.commit()
        return row


def update_post(
    conn: psycopg.Connection,
    post_id: int,
    user_id: int,
    payload: dict,
) -> dict | None:
    allowed_keys = {"title", "content", "is_anonymous", "bot_id"}
    updates = {key: value for key, value in payload.items() if key in allowed_keys and value is not None}

    if "bot_id" in updates:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM bots WHERE id = %s AND user_id = %s", (updates["bot_id"], user_id))
            if not cur.fetchone():
                raise ValueError("유효하지 않은 봇입니다.")

    if not updates:
        return get_post(conn, post_id, user_id)

    fields = [f"{key} = %s" for key in updates]
    values = list(updates.values())
    values.extend([post_id, user_id])

    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE sns_posts
            SET {', '.join(fields)},
                updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id,
                      user_id,
                      bot_id,
                      title,
                      content,
                      is_anonymous,
                      created_at,
                      updated_at
            """,
            tuple(values),
        )
        row = cur.fetchone()
        conn.commit()
        return row


def delete_post(conn: psycopg.Connection, post_id: int, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sns_posts WHERE id = %s AND user_id = %s", (post_id, user_id))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
