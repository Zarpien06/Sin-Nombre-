import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sin_nombre.db")
APP_SECRET = os.getenv("APP_SECRET", "dev-only-change-me")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
