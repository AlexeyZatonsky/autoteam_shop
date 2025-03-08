from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List



load_dotenv()

class Settings(BaseSettings):
    
    DB_USER: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_PASS: str
    SECRET_AUTH: str
    SERVER_HOST: str
    SERVER_PORT: int
    TG_BOT_TOKEN: str
    ADMIN_IDS: List[int]
    API_URL: str
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()