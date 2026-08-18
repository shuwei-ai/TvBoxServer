import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "")
    mongo_database: str = os.getenv("MONGO_DATABASE", "tvbox_ai")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-only-change-me-at-least-32-bytes")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    api_key_pepper: str = os.getenv("API_KEY_PEPPER", os.getenv("JWT_SECRET", "dev-only-change-me-at-least-32-bytes"))
    bootstrap_admin_username: str = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "")
    bootstrap_admin_password: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    cors_origins: tuple = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()) or ("*",)
    root_path: str = os.getenv("ROOT_PATH", "")
    dreamauth_base_url: str = os.getenv("DREAMAUTH_BASE_URL", "https://guangyingzhimeng.dpdns.org/kite-hub").rstrip("/")
    dreamauth_app_code: str = os.getenv("DREAMAUTH_APP_CODE", "")
    dreamauth_access_key: str = os.getenv("DREAMAUTH_ACCESS_KEY", os.getenv("DREAMAUTH_AK", ""))
    dreamauth_secret_key: str = os.getenv("DREAMAUTH_SECRET_KEY", os.getenv("DREAMAUTH_SK", ""))
    admin_openids: tuple = tuple(x.strip() for x in os.getenv("ADMIN_OPENIDS", "").split(",") if x.strip())


settings = Settings()
