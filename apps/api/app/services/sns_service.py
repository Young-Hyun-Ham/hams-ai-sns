import psycopg


def list_public_posts(conn: psycopg.Connection) -> list[dict]:
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
                   b.name AS bot_name,
                   (
                     SELECT COUNT(*)::INT
                     FROM sns_comments c
                     WHERE c.post_id = p.id
                   ) AS comment_count
            FROM sns_posts p
            LEFT JOIN bots b ON b.id = p.bot_id
            ORDER BY p.created_at DESC
            """,
        )
        return list(cur.fetchall())


def get_post_by_id(conn: psycopg.Connection, post_id: int) -> dict | None:
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
                   b.name AS bot_name,
                   (
                     SELECT COUNT(*)::INT
                     FROM sns_comments c
                     WHERE c.post_id = p.id
                   ) AS comment_count
            FROM sns_posts p
            LEFT JOIN bots b ON b.id = p.bot_id
            WHERE p.id = %s
            """,
            (post_id,),
        )
        return cur.fetchone()


def is_post_owner(conn: psycopg.Connection, post_id: int, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM sns_posts WHERE id = %s AND user_id = %s", (post_id, user_id))
        return cur.fetchone() is not None


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
    if not is_post_owner(conn, post_id, user_id):
        return None

    allowed_keys = {"title", "content", "is_anonymous", "bot_id"}
    updates = {key: value for key, value in payload.items() if key in allowed_keys and value is not None}

    if "bot_id" in updates:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM bots WHERE id = %s AND user_id = %s", (updates["bot_id"], user_id))
            if not cur.fetchone():
                raise ValueError("유효하지 않은 봇입니다.")

    if not updates:
        return get_post_by_id(conn, post_id)

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


def list_comments(conn: psycopg.Connection, post_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.post_id, c.user_id, c.content, c.created_at, c.updated_at
            FROM sns_comments c
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
            """,
            (post_id,),
        )
        return list(cur.fetchall())


def create_comment(conn: psycopg.Connection, post_id: int, user_id: int, content: str) -> dict:
    if not get_post_by_id(conn, post_id):
        raise ValueError("게시글을 찾을 수 없습니다.")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sns_comments (post_id, user_id, content)
            VALUES (%s, %s, %s)
            RETURNING id, post_id, user_id, content, created_at, updated_at
            """,
            (post_id, user_id, content),
        )
        row = cur.fetchone()
        conn.commit()
        return row


def update_comment(conn: psycopg.Connection, comment_id: int, user_id: int, content: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE sns_comments
            SET content = %s,
                updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id, post_id, user_id, content, created_at, updated_at
            """,
            (content, comment_id, user_id),
        )
        row = cur.fetchone()
        conn.commit()
        return row


def delete_comment(conn: psycopg.Connection, comment_id: int, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM sns_comments
            WHERE id = %s AND user_id = %s
            """,
            (comment_id, user_id),
        )
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
