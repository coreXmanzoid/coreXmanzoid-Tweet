import re

from flask import Blueprint, current_app, make_response, render_template, request, send_from_directory
from flask_login import login_required, current_user

from app.services.account_service import AccountService

main_bp = Blueprint("main", __name__)


def is_mobile_request():
    user_agent = request.headers.get("User-Agent", "")
    mobile_pattern = r"Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile"
    return re.search(mobile_pattern, user_agent, re.IGNORECASE) is not None

@main_bp.route("/")
def home():
    return render_template("index.html")

@main_bp.route("/about")
def about():
    return render_template("about.html")

@main_bp.route("/privacy-policy")
def privacy_policy():
    return render_template("privacyPolicy.html")

@main_bp.route("/terms-of-service")
def terms_of_service():
    return render_template("termsOfService.html")


@main_bp.route("/firebase-messaging-sw.js")
def firebase_messaging_sw():
    response = make_response(
        send_from_directory(current_app.static_folder, "firebase-messaging-sw.js")
    )
    response.headers["Content-Type"] = "application/javascript; charset=utf-8"
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@main_bp.route("/home", methods=["GET", "POST"])
@login_required
def homepage():

    is_user_verified = current_user.status == "VERIFIED" or current_user.status == "PRO"
    mobile_accounts = AccountService.random_accounts()

    if is_mobile_request():
        return render_template(
            "mobile-home.html",
            is_user_verified=is_user_verified,
            accounts=mobile_accounts,
        )

    return render_template(
        "home.html",
        is_user_verified=is_user_verified
    )


@main_bp.route("/mobile-home", methods=["GET", "POST"])
@login_required
def mobile_homepage():
    is_user_verified = current_user.status == "VERIFIED" or current_user.status == "PRO"
    mobile_accounts = AccountService.random_accounts()
    return render_template(
        "mobile-home.html",
        is_user_verified=is_user_verified,
        accounts=mobile_accounts,
    )
