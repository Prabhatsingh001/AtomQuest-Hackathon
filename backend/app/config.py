"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL connection string.
        REDIS_URL: Redis broker connection string.
        SECRET_KEY: Secret key for JWT signature.
        ALGORITHM: Encryption algorithm for JWT.
        ACCESS_TOKEN_EXPIRE_MINUTES: Expiration time for access tokens in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS: Expiration time for refresh tokens in days.
        SMTP_HOST: SMTP server hostname for sending emails.
        SMTP_PORT: SMTP port number.
        SMTP_USER: SMTP authentication username.
        SMTP_PASSWORD: SMTP authentication password.
        HR_EMAIL: Default HR recipient email address.
        FRONTEND_URL: Allowed origin URL for CORS configuration.
        ENVIRONMENT: Application deployment environment mode.
    """

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    HR_EMAIL: str = ""
    FRONTEND_URL: str
    ENVIRONMENT: str

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Retrieve the cached application settings singleton.

    Returns:
        Settings: The loaded application settings instance.
    """
    return Settings()
