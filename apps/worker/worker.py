import os
import time
from datetime import datetime, UTC


def main() -> None:
    poll_seconds = int(os.getenv("WORKER_POLL_SECONDS", "10"))
    while True:
        print(f"[{datetime.now(UTC).isoformat()}] worker heartbeat (poll={poll_seconds}s)", flush=True)
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
