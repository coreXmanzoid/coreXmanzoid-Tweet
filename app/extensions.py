from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth


# Base model class for SQLAlchemy
class Base(DeclarativeBase):
    pass


# Database instance
db = SQLAlchemy(model_class=Base)

# Login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # where to redirect if not logged in

# OAuth instance
oauth = OAuth()