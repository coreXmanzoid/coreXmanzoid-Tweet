from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required


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
