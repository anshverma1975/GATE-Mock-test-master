import os

class Config:
    SECRET_KEY = os.environ.get("MAD1_project_secret_key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///quiz_master.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False