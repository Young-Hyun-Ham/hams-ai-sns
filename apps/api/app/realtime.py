import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket

from app.db import get_connection


class RealtimeManager:
    def __init__(self) -> None:
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._last_log_id = 0

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.connections[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            clients = self.connections.get(user_id)
            if not clients:
                return
            clients.discard(websocket)
            if not clients:
                self.connections.pop(user_id, None)

    async def broadcast_activity_log(self, user_id: int, payload: dict) -> None:
        async with self._lock:
            clients = list(self.connections.get(user_id, set()))

        for ws in clients:
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception:  # noqa: BLE001
                await self.disconnect(user_id, ws)

    def fetch_new_logs(self) -> list[dict]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT l.id, b.user_id, l.bot_id, l.job_id, l.job_type, l.result_status, l.message, l.executed_at
                    FROM activity_logs l
                    INNER JOIN bots b ON b.id = l.bot_id
                    WHERE l.id > %s
                    ORDER BY l.id ASC
                    LIMIT 100
                    """,
                    (self._last_log_id,),
                )
                rows = list(cur.fetchall())

        if rows:
            self._last_log_id = rows[-1]["id"]

        return rows


manager = RealtimeManager()


async def activity_log_poller(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        rows = manager.fetch_new_logs()
        for row in rows:
            payload = {
                "type": "activity_log",
                "data": {
                    "id": row["id"],
                    "bot_id": row["bot_id"],
                    "job_id": row["job_id"],
                    "job_type": row["job_type"],
                    "result_status": row["result_status"],
                    "message": row["message"],
                    "executed_at": row["executed_at"].isoformat(),
                },
            }
            await manager.broadcast_activity_log(row["user_id"], payload)

        await asyncio.sleep(1)
