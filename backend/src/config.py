from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    APP_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str
    COMPOSE_PROJECT_NAME: str
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
        env_file_encoding="utf-8"
    )
    
settings = Settings()

def get_db_config():
    return {
            "uri": f"bolt://{settings.DB_HOST}:{settings.DB_PORT}",
            'user': settings.DB_USER,
            'pass': settings.DB_PASSWORD
        }
    
def get_auth_data():
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}