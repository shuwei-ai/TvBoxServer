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
    cors_origins: tuple = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip())


settings = Settings()
