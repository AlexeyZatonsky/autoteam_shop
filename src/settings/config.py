from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List



load_dotenv()

class Settings(BaseSettings):
    
    DB_USER: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_PASS: str
    SECRET_AUTH: str
    SERVER_HOST: str = "localhost"
    SERVER_PORT: int = 1088
    TG_BOT_TOKEN: str
    ADMIN_IDS: str  # Строка с ID через запятую
    API_URL: str = "http://localhost:1088"
    
    S3_BUCKET_NAME: str
    S3_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    
    # Ключ API для бота
    BOT_API_KEY: str = "your-secret-api-key"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def admin_ids(self) -> List[int]:
        """Преобразует строку с ID админов в список целых чисел"""
        return [int(id_str) for id_str in self.ADMIN_IDS.split(',') if id_str.strip()]
    
    @property
    def ADMIN_USER_ID(self) -> str:
        """Возвращает ID первого администратора из списка"""
        admin_ids = self.admin_ids
        if not admin_ids:
            raise ValueError("Не указаны ID администраторов в настройках")
        return str(admin_ids[0])
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()