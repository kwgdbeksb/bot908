import os
from dataclasses import dataclass


@dataclass
class BotConfig:
    token: str
    app_id: int
    owner_id: int
    guild_id: int | None
    sync_global: bool
    yt_cookies: str | None
    lavalink_host: str
    lavalink_port: int
    lavalink_password: str


def load_config() -> BotConfig:
    # Allow environment variables or .env; dotenv optional to avoid runtime crash if missing
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        # Fallback: manually parse .env if present
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    os.environ.setdefault(key, val)
        except Exception:
            pass

    def getenv_any(keys: list[str], default: str | None = None) -> str | None:
        for k in keys:
            v = os.getenv(k)
            if v is not None and v.strip() != "":
                return v.strip()
        return default

    token = getenv_any(["DISCORD_TOKEN", "TOKEN", "BOT_TOKEN"], "") or ""
    app_id_val = getenv_any(["APP_ID", "APPLICATION_ID", "CLIENT_ID"], "0") or "0"
    owner_id_val = getenv_any(["OWNER_ID", "OWNER", "BOT_OWNER"], "0") or "0"
    guild_id_env = getenv_any(["GUILD_ID", "SERVER_ID", "GUILD"])  # may be empty
    app_id = int(app_id_val) if app_id_val.isdigit() else 0
    owner_id = int(owner_id_val) if owner_id_val.isdigit() else 0
    guild_id = int(guild_id_env) if guild_id_env and guild_id_env.isdigit() else None
    sync_global = getenv_any(["SYNC_GLOBAL"], "false").lower() in ("true", "1", "yes")
    yt_cookies = getenv_any(["YT_COOKIES", "YOUTUBE_COOKIES"])

    # Lavalink configuration
    lavalink_host = getenv_any(["LAVALINK_HOST"], "localhost") or "localhost"
    lavalink_port_str = getenv_any(["LAVALINK_PORT"], "2333") or "2333"
    lavalink_port = int(lavalink_port_str) if lavalink_port_str.isdigit() else 2333
    lavalink_password = getenv_any(["LAVALINK_PASSWORD"], "youshallnotpass") or "youshallnotpass"

    # Debug: log the Lavalink password (remove in production)
    print(f"Debug: Lavalink password loaded: {lavalink_password}")

    # Validation
    if not token:
        raise ValueError("DISCORD_TOKEN is required but not found in environment variables or .env file")
    if not app_id:
        raise ValueError("APP_ID is required but not found in environment variables or .env file")
    if not owner_id:
        raise ValueError("OWNER_ID is required but not found in environment variables or .env file")

    return BotConfig(
        token=token,
        app_id=app_id,
        owner_id=owner_id,
        guild_id=guild_id,
        sync_global=sync_global,
        yt_cookies=yt_cookies,
        lavalink_host=lavalink_host,
        lavalink_port=lavalink_port,
        lavalink_password=lavalink_password,
    )