from pydantic import Field, SecretStr, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SMSC_LOGIN: str
    SMSC_PASSWORD: SecretStr
    SENDER: EmailStr
    EMAILS: str
    MESSAGE_SUBJECT: str = Field(default='Погода')
    MESSAGE_LIFE_SPAN: int = Field(default=1)

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


ENV = Settings()
