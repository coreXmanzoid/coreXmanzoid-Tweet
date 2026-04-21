from flask import (
    Blueprint,
    redirect,
    render_template,
    url_for,
    request,
    jsonify,
    flash,
    send_file,
)
from flask_login import login_required
from app.extensions import db
from flask_login import current_user, logout_user
from app.models.users import UserData
from app.services.setting_service import SettingService
from app.services.data_downloading_service import DownloadData
from app.services.email_service import EmailService
from app.services.auth_service import AuthService
from datetime import datetime

setting_bp = Blueprint("setting", __name__)

VALID_SECTIONS = {
    "profile-info",
    "account-info",
    "change-password",
    "privacy-setting",
    "notifications-setting",
    "support",
    "delete-account",
}


@setting_bp.route("/setting")
@login_required
def setting_index():
    return redirect(url_for("setting.setting", section="profile-info"))


@setting_bp.route("/setting/<string:section>")
@login_required
def setting(section):
    if section not in VALID_SECTIONS:
        return redirect(url_for("setting.setting", section="profile-info"))

    return render_template("setting.html", section=section)


@setting_bp.route("/setting/profile-setting", methods=["GET", "POST"])
@login_required
def profile_setting():
    if request.method == "POST":
        data = request.get_json()
        user_id = data["user_id"]
        user = db.session.get(UserData, user_id)
        if user:
            new_name = data["new_name"]
            new_username = data["new_username"]
            new_username = (
                new_username.split("@")[1]
                if new_username.startswith("@")
                else new_username
            )
            new_contact = data["new_contact"]
            new_bio = data["new_bio"]
            
            if current_user.name != new_name:
                SettingService.change_name(user, new_name)
                flash("Name update Successfully", "success")

            temp_user = AuthService.username_exists(new_username)
            if current_user.username != new_username:
                if temp_user:
                    flash("Username Already Exists", "error")
                else:
                    SettingService.change_username(user, new_username)
                    flash("Username Updated Successfully", "success")

            if current_user.contact != new_contact:
                SettingService.change_contact(user, new_contact)
                flash("Contact Number updated Successfully", "success")

            current_bio = current_user.get_setting("profile-info", "bio", "")
            if current_bio != new_bio:
                SettingService.change_bio(user, new_bio)
                flash("Bio Updated...", "success")

            return jsonify({"status": "success", "section": "profile-info"})
        return jsonify({"status": "error", "message": "User Not Found"})
    return jsonify({"status": "error", "message": "Not a valid request"})


@setting_bp.route("/setting/account-setting", methods=["GET", "POST"])
@login_required
def account_setting():
    if request.method == "POST":
        data = request.get_json()
        user_id = data["user_id"]
        user = db.session.get(UserData, user_id)
        if user:
            new_email = data["new_email"]
            new_birthdate = data["new_birthdate"]
            new_website = data["new_website"]
            new_about = data["new_about"]

            if current_user.email != new_email:
                if not EmailService.validate_email(str(new_email)):
                    flash("Please Enter a Valid Email", "error")               
                elif AuthService.email_exists(new_email):
                    flash("Email Already Exists", "error")                
                else:
                    SettingService.change_email(user, new_email)
                    flash("Email Updated Successfully", "success")
            new_birthdate = (
                datetime.strptime(new_birthdate, "%Y-%m-%d").date()
                if new_birthdate
                else None
            )
            if current_user.birth_date != new_birthdate:
                SettingService.change_birthdate(user, new_birthdate)
                flash("Birthdate Updated Successfully", "success")

            current_about = user.get_setting("account-info", "about", "")
            if current_about != new_about:
                SettingService.change_about(user, new_about)
                flash("About-info Added Successfully", "success")
            current_website = user.get_setting("account-info", "website", "")
            if current_website != new_website:
                SettingService.change_website(user, new_website)
                flash("Website added Successfully.", "success")
            return jsonify({"status": "success", "section": "account-info"})
        return jsonify({"status": "error", "message": "User Not Found"})
    return jsonify({"status": "error", "message": "Not a valid request"})


@setting_bp.route("/setting/password-setting", methods=["GET", "POST"])
@login_required
def password_setting():
    if request.method == "POST":
        data = request.get_json()
        user_id = data["user_id"]
        user = db.session.get(UserData, user_id)
        if user:
            current_password = data["current_password"]
            new_password = data["new_password"]
            confirm_password = data["confirm_password"]
            is_changeable = SettingService.verify_password_change(
                user, current_password, new_password, confirm_password
            )
            if is_changeable:
                SettingService.change_password(user, new_password)
                flash("Password Changed Successfully.", "success")
            else:
                flash("Invalid attempt to password change. Please try again.", "error")
            return jsonify({"status": "success", "section": "change-password"})
        return jsonify({"status": "error", "message": "User Not Found"})
    return jsonify({"status": "error", "message": "Not a valid request"})


@setting_bp.route("/setting/privacy-settings", methods=["GET", "POST"])
@login_required
def privacy_setting():
    if request.method == "POST":
        data = request.get_json()
        user_id = data["user_id"]
        user = db.session.get(UserData, user_id)
        if user:
            privacy_status = data["private_account"]
            birthdate_status = data["birthdate_status"]
            bio_status = data["bio_status"]
            myStatus = data["myStatus"]
            current_privacy_status = user.get_setting(
                "privacy-setting", "private_account", ""
            )
            if current_privacy_status != privacy_status:
                SettingService.change_privacy_status(user, privacy_status)
            current_birthdate_status = user.get_setting(
                "privacy-setting", "show_birthdate", ""
            )
            if current_birthdate_status != birthdate_status:
                SettingService.change_birthdate_status(user, birthdate_status)

            current_bio_status = user.get_setting("privacy-setting", "show_bio", "")
            if current_bio_status != bio_status:
                SettingService.change_bio_status(user, bio_status)

            current_myStatus = user.get_setting("privacy-setting", "show_status", "")
            if current_myStatus != myStatus:
                SettingService.change_myStatus_status(user, myStatus)

            flash("Privacy Updated Successfully", "success")
            return jsonify({"status": "success", "section": "account-info"})
        return jsonify({"status": "error", "message": "User Not Found"})
    return jsonify({"status": "error", "message": "Not a valid request"})


@setting_bp.route("/setting/notifications-settings", methods=["GET", "POST"])
@login_required
def notifications_setting():
    if request.method == "POST":
        data = request.get_json()
        user_id = data["user_id"]
        user = db.session.get(UserData, user_id)
        if user:
            push_notifications = data["push_notifications"]
            email_notifications = data["email_notifications"]
            mentions = data["mentions"]
            reposts = data["reposts"]
            likes_comments = data["likes_comments"]
            new_followers = data["new_followers"]
            current_push_notification = user.get_setting(
                "notifications-setting", "push_notifications", "")
            if current_push_notification != push_notifications:
                SettingService.change_push_notifications(user, push_notifications)

            current_email_notifications = user.get_setting(
                "notifications-setting", "email_notifications", ""
            )
            if current_email_notifications != email_notifications:
                SettingService.change_email_notifications(user, email_notifications)

            current_new_followers = user.get_setting("notifications-setting", "new_followers", "")
            if current_new_followers != new_followers:
                SettingService.change_newFollower_notifications(user, new_followers)

            current_mentions = user.get_setting("notifications-setting", "mentions", "")
            if current_mentions != mentions:
                SettingService.change_mentions_notifications(user, mentions)

            current_reposts = user.get_setting("notifications-setting", "reposts", "")
            if current_reposts != reposts:
                SettingService.change_reposts_notifications(user, reposts)

            current_likes_comments = user.get_setting(
                "notifications-setting", "likes_comments", ""
            )
            if current_likes_comments != likes_comments:
                SettingService.change_likeComments_notifications(user, likes_comments)

            flash("Notifications Setting Updated Successfully", "success")
            return jsonify({"status": "success", "section": "account-info"})
        return jsonify({"status": "error", "message": "User Not Found"})
    return jsonify({"status": "error", "message": "Not a valid request"})


@setting_bp.route("/setting/support-setting", methods=["POST"])
@login_required
def support_setting():
    data = request.get_json()
    user_id = data["user_id"]
    user = db.session.get(UserData, user_id)
    if user:
        new_theme = "light" if data.get("theme") == "light" else "dark"
        current_theme = user.get_setting("support", "theme", "dark")
        current_theme = "light" if current_theme == "light" else "dark"
        if current_theme != new_theme:
            SettingService.change_theme(user, new_theme)
            flash("Theme Changed Successfully.", "success")
        return jsonify({"status": "success", "section": "support"})
    return jsonify({"status": "error", "message": "User Not Found"})


@setting_bp.route("/setting/download-account-data/<int:id>")
@login_required
def download_account_data(id):
    if id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    user = db.session.get(UserData, id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    account_info = DownloadData.account_info(user)
    user_posts = DownloadData.user_posts(user)
    setting_info = DownloadData.setting_info(user)
    zip_file = DownloadData.write_zip(account_info, user_posts, setting_info)
    flash("File Available to Download", "info")
    return send_file(
        zip_file,
        download_name=f"{current_user.username}_ChatFlick_datafile.zip",
        as_attachment=True,
        mimetype="application/zip",
    )


@setting_bp.route("/setting/create-report", methods=["GET", "POST"])
@login_required
def create_report():
    if request.method == "POST":
        data = request.get_json()
        user_id = data["user_id"]
        message = data["message"]
        SettingService.create_report(user_id, message)
        flash("Report Submitted Successfully.", "success")
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "invalid request"})


@setting_bp.route("/setting/create-support-request", methods=["GET", "POST"])
@login_required
def create_support_request():
    if request.method == "POST":
        data = request.get_json()
        user_id = data["user_id"]
        category = data["category"]
        message = data["message"]
        SettingService.create_support_request(user_id, category, message)
        flash(
            "Your Request is Submitted Successfully. We will try to respond you as soon as possible.",
            "success",
        )
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "invalid request"})

@setting_bp.route("/danger-zone/<int:st>", methods=["POST"])
@login_required
def danger_zone(st):
    if request.method == 'POST':
        data = request.get_json()
        user_id = data["user_id"]
        user = db.session.get(UserData, user_id)
        if not user or user.id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        if st == 1:
            SettingService.deactivate_account(user)
            logout_user()
            flash("Account is Deactivated.", "info")
            return jsonify({"status": "success", "message": "account deactivated"})
        if st == 2:
            SettingService.delete_account(user)
            logout_user()
            flash("Account is deleted completely from DataBase.", "info")
            return jsonify({"status": "success", "message": "account deleted successfully"})
    return jsonify({"status": "error", "message": "invalid request"})
            
