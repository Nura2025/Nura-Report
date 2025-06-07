from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
from pathlib import Path

# تحميل المتغيرات البيئية
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(..., env="DATABASE_URL")
    algorithm: str = "HS256"


    model_config = {
        "env_file": dotenv_path
    }

settings = Settings()

print("Loaded settings:", settings.model_dump())  # طباعة القيم للتأكد من تحميلها
