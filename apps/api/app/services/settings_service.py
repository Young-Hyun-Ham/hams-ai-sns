import psycopg

DEFAULT_MAX_COMMENT_DEPTH = 3
MIN_COMMENT_DEPTH = 1
MAX_COMMENT_DEPTH = 10


def _clamp_depth(value: int) -> int:
    return max(MIN_COMMENT_DEPTH, min(MAX_COMMENT_DEPTH, value))


def get_max_comment_depth(conn: psycopg.Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM app_settings WHERE key = 'max_comment_depth'")
        row = cur.fetchone()
        if not row:
            return DEFAULT_MAX_COMMENT_DEPTH

    try:
        return _clamp_depth(int(row["value"]))
    except (ValueError, TypeError):
        return DEFAULT_MAX_COMMENT_DEPTH


def set_max_comment_depth(conn: psycopg.Connection, depth: int) -> int:
    value = _clamp_depth(depth)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_settings (key, value)
            VALUES ('max_comment_depth', %s)
            ON CONFLICT (key)
            DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            RETURNING value
            """,
            (str(value),),
        )
        row = cur.fetchone()
        conn.commit()

    return int(row["value"]) if row else value
