from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = "teachcare-research-prototype"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'teachcare.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
