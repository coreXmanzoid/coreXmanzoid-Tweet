import os
from flask import Flask

from app.extensions import db, login_manager, oauth as oauth_client

from app.routes.notification_routes import notification_bp
from app.firebase.firebase_config import init_firebase
from app.routes.profile_routes import profile_bp
from app.routes.post_routes import post_bp
from app.routes.ai_routes import ai_bp
from app.routes.auth_routes import auth_bp
from app.routes.main_routes import main_bp
from app.routes.comment_routes import comment_bp
from app.routes.account_routes import account_bp
from app.routes.setting_routes import setting_bp
def create_app():

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
    app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coreXmanzoidTweet.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    oauth_client.init_app(app)
    init_firebase()

    app.register_blueprint(notification_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(post_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(setting_bp)

    with app.app_context():
        from app import models
        from app import auth
        from app.oauth import google_oauth
        db.create_all()

    return app
