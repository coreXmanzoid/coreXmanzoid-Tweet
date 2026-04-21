from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user

pricing_bp = Blueprint("pricing", __name__)

@pricing_bp.route("/pricing")
def pricing():
    user = current_user if current_user.is_authenticated else None
    return render_template("pricing.html", user=user)
