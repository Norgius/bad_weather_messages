from pydantic import Field, SecretStr, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisConfig(BaseSettings):
    HOST: str
    PORT: int
    PASSWORD: SecretStr


class Settings(BaseSettings):
    SMSC_LOGIN: str
    SMSC_PASSWORD: SecretStr
    SENDER: EmailStr
    EMAILS: str
    MESSAGE_SUBJECT: str = Field(default='Погода')
    MESSAGE_LIFE_SPAN: int = Field(default=1)

    REDIS: RedisConfig

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        case_sensitive=True,
        env_nested_delimiter='__',
        validate_default=True
    )


ENV = Settings()
