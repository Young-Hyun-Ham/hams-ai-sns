import json
import urllib.error
import urllib.parse
import urllib.request


class AIModelServiceError(Exception):
    pass


def _request_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(url=url, method="GET", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise AIModelServiceError(f"model list fetch failed: {exc}") from exc


def list_models(ai_provider: str, api_key: str) -> list[str]:
    provider = ai_provider.lower()
    key = api_key.strip()
    if not key:
        raise AIModelServiceError("api_key가 비어 있습니다.")

    if provider == "gpt":
        payload = _request_json(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        rows = payload.get("data", [])
        models = [row.get("id", "") for row in rows if isinstance(row, dict)]
        return sorted([m for m in models if m.startswith(("gpt-", "o", "omni"))])[:50] or sorted(models)[:50]

    if provider == "gemini":
        encoded = urllib.parse.quote(key)
        payload = _request_json(f"https://generativelanguage.googleapis.com/v1beta/models?key={encoded}")
        rows = payload.get("models", [])
        models = []
        for row in rows:
            name = row.get("name", "")
            if name.startswith("models/"):
                name = name.split("/", 1)[1]
            if "generateContent" in row.get("supportedGenerationMethods", []) or "gemini" in name:
                models.append(name)
        return sorted(set(models))[:50]

    if provider == "claude":
        payload = _request_json(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        rows = payload.get("data", [])
        models = [row.get("id", "") for row in rows if isinstance(row, dict)]
        return sorted([m for m in models if m])[:50]

    if provider == "mock":
        return ["mock-v1"]

    raise AIModelServiceError("지원하지 않는 ai_provider 입니다.")
