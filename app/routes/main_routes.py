from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return render_template("index.html")

@main_bp.route("/home", methods=["GET", "POST"])
@login_required
def homepage():

    is_user_verified = current_user.status == "VERIFIED" or current_user.status == "PRO"
    return render_template(
        "home.html",
        is_user_verified=is_user_verified
    )
