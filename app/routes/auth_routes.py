from datetime import date

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for, flash
from flask_login import login_required, current_user, login_user

from app.extensions import db, oauth
from app.oauth import google_oauth
from app.services.auth_service import AuthService
from app.services.captcha_service import CaptchaService
from app.services.email_service import EmailService
from app.services.google_auth_service import GoogleAuthService
from app.utils.username import validate_username

auth_bp = Blueprint("auth", __name__)


def get_google_client():
    return oauth.create_client("google")


@auth_bp.route("/email-verification", methods=["POST"])
@login_required
def email_verification():
    user = current_user

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    email_sent = AuthService.send_email_verification(user)

    if not email_sent:
        current_app.logger.error(
            "Email verification message could not be sent to user_id=%s email=%s",
            user.id,
            user.email,
        )
        return jsonify({"status": "error", "message": "Email could not be sent"}), 500

    return jsonify({"status": "success"})


@auth_bp.route("/verify-email/<token>")
def verify_email_with_token(token):
    user = AuthService.verify_email_token(token)

    if not user:
        return "Verification link expired or invalid.", 400

    if user.status == "VERIFIED":
        return "Email already verified."

    user.status = "VERIFIED"
    db.session.commit()

    return redirect(url_for("main.homepage"))


@auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("auth.authorize_google", _external=True)
    google = get_google_client()
    return google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/authorized")
def authorize_google():
    google = get_google_client()
    try:
        token = google.authorize_access_token()
    except Exception as e:
        flash("Google sign in failed. Please try again.")
        print("GOOGLE AUTH ERROR:", e)
        return redirect(url_for("auth.login"))

    user_info = token.get("userinfo") if token else None

    if not user_info:
        user_info = google.get(
            "https://openidconnect.googleapis.com/v1/userinfo"
        ).json()

    user = GoogleAuthService.get_or_create_user(user_info)

    if not user:
        flash("Google account email is unavailable.")
        return redirect(url_for("auth.signup", st=0))

    login_user(user)

    return redirect(url_for("main.homepage"))


@auth_bp.route("/signup/<int:st>", methods=["GET", "POST"])
def signup(st):
    if request.method == "POST":
        if st == 1:
            username = request.get_json().get("username")

            if AuthService.username_exists(username):
                return jsonify({"status": "abondonded"})

            return jsonify({"status": "success"})

        captcha_token = request.form.get("cf-turnstile-response")

        if not CaptchaService.verify_turnstile(captcha_token, request.remote_addr):
            flash("CAPTCHA verification failed.")
            return redirect(url_for("auth.signup", st=0))

        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("pin")

        birth_date_str = request.form.get("birthDate")

        birth_date = date.fromisoformat(birth_date_str) if birth_date_str else None

        if AuthService.email_exists(email):
            flash("Email already exists. Login instead")
            return redirect(url_for("auth.login"))

        if AuthService.username_exists(username):
            flash("Username already taken.")
            return redirect(url_for("auth.signup", st=0))
        if not validate_username(username):
            flash("Username can only contain letters, numbers, underscores and dots.", "error")
            return redirect(url_for("auth.signup", st=0))
        AuthService.create_user(name, username, email, birth_date, password)

        flash("Account created successfully. Please verify your email.")

        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        captcha_token = request.form.get("cf-turnstile-response")

        if not CaptchaService.verify_turnstile(captcha_token, request.remote_addr):
            flash("CAPTCHA verification failed.")
            return redirect(url_for("auth.login"))

        username = request.form.get("username")
        password = request.form.get("pin")
        remember = request.form.get("rememberMe") == "on"
        user = AuthService.authenticate(username, password)

        if not user:
            flash("Invalid credentials.")
            return redirect(url_for("auth.login"))

        if user:
            session['user_id'] = user.id

        if remember:
            session.permanent = True   # lasts 7 days
        else:
            session.permanent = False  # ends when browser closes

        login_user(user)

        return redirect(url_for("main.homepage"))

    return render_template("login.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        data = request.get_json()

        captcha_token = data.get("cf-turnstile-response")

        if not CaptchaService.verify_turnstile(captcha_token, request.remote_addr):
            return jsonify({"status": "error", "message": "CAPTCHA failed"}), 400

        email = data.get("email")

        user = AuthService.email_exists(email)

        if user:
            token = AuthService.create_reset_token(user.id)

            reset_link = url_for(
                "auth.reset_password_with_token",
                token=token,
                _external=True,
            )

            email_sent = EmailService.send_link_email(email, reset_link, st=2)

            if not email_sent:
                current_app.logger.error(
                    "Password reset email could not be sent to user_id=%s email=%s",
                    user.id,
                    email,
                )

        return jsonify(
            {
                "status": "success",
                "message": "If this email exists, a reset link has been sent.",
            }
        )

    return render_template("resetPassword.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_with_token(token):
    user = AuthService.verify_reset_token(token)

    if not user:
        flash("This reset link is invalid or expired.")
        return redirect(url_for("auth.reset_password"))

    if request.method == "POST":
        data = request.get_json()

        new_password = data.get("newPassword")
        confirm_password = data.get("confirmNewPassword")

        if new_password != confirm_password:
            return jsonify({"status": "error", "message": "Passwords do not match"})

        AuthService.reset_password(user, new_password)

        return jsonify(
            {"status": "success", "message": "Password reset successfully"}
        )

    return render_template("resetPassword.html")
