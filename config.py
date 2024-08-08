﻿from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='')

    telegram_bot_api_token: str

settings = Settings()