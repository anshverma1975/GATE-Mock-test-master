import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "mere_desh_ki_dhartiiiiiiii")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///quiz_master.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False