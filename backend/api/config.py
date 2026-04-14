from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+psycopg://pila:pilapass@localhost:5432/pila_db"
    TEST_DATABASE_URL: str = "postgresql+psycopg://pila:pilapass@localhost:5432/pila_test"

    # Redis
    REDIS_URL: str = "redis://:redispass@localhost:6379/0"

    # Security
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES is kept for backward compatibility but superseded
    # by PIN_ACCESS_TOKEN_EXPIRE_MINUTES for the PIN verify flow.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Dual-session settings (Approach B)
    PASSWORD_SESSION_DAYS: int = 30           # lifetime of opaque password session
    PIN_ACCESS_TOKEN_EXPIRE_MINUTES: int = 360  # 6-hour access JWT after PIN verify

    # Developer internal API
    DEVELOPER_API_KEY: str = "dev_api_key_12345"

    # App
    APP_NAME: str = "Pila Studio Management"
    ENVIRONMENT: str = "development"


settings = Settings()
