from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Activity Registration and Funding Audit Management Platform"
    app_env: str = "development"

    database_url: str = "postgresql+psycopg://activity_user:activity_password@postgres:5432/activity_audit"

    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120

    uploads_dir: str = "/app/uploads"
    backups_dir: str = "/app/backups"
    reports_dir: str = "/app/backups/reports"
    security_dir: str = "/app/backups/security"

    similarity_check_enabled: bool = False

    alert_approval_rate_min: float = 0.4
    alert_correction_rate_max: float = 0.5
    alert_overspending_rate_max: float = 0.2

    seed_admin_username: str = "admin"
    seed_admin_password: str = "Admin@123456"
    seed_admin_full_name: str = "System Administrator"

    config_encryption_key: str | None = None


settings = Settings()
