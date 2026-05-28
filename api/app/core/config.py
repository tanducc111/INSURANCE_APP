from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Insurance Management System API"
    API_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "local"
    DATABASE_URL: str = (
        "postgresql+psycopg://insurance_user:insurance_password"
        "@localhost:5432/insurance_app"
    )
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SEED_ADMIN_EMAIL: str = "admin@insurance.local"
    SEED_ADMIN_PASSWORD: str = "ChangeMe123!"
    SEED_ADMIN_FULL_NAME: str = "System Administrator"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
