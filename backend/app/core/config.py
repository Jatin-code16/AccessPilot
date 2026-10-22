from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_origin: str = "http://127.0.0.1:5173"
    allow_loopback: bool = True
    sites_root: Path = Path(__file__).resolve().parents[3] / "sites"
    work_root: Path = Path(__file__).resolve().parents[3] / "work"
    axe_path: Path = Path(__file__).resolve().parents[2] / "vendor" / "axe.min.js"
    browser_timeout_ms: int = 30000
    approval_ttl_seconds: int = 900
    ai_provider: str = "none"
    ai_base_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None

    @property
    def model_configured(self) -> bool:
        return all((self.ai_provider != "none", self.ai_base_url, self.ai_api_key, self.ai_model))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    values: dict[str, object] = {}
    environment_names = {
        "backend_host": "BACKEND_HOST",
        "backend_port": "BACKEND_PORT",
        "frontend_origin": "FRONTEND_ORIGIN",
        "allow_loopback": "ALLOW_LOOPBACK",
        "ai_provider": "AI_PROVIDER",
        "ai_base_url": "AI_BASE_URL",
        "ai_api_key": "AI_API_KEY",
        "ai_model": "AI_MODEL",
    }
    for field_name, environment_name in environment_names.items():
        value = os.getenv(environment_name)
        if value is not None:
            values[field_name] = value
    if "backend_port" in values:
        values["backend_port"] = int(str(values["backend_port"]))
    if "allow_loopback" in values:
        values["allow_loopback"] = str(values["allow_loopback"]).lower() in {"1", "true", "yes"}
    return Settings(**values)
