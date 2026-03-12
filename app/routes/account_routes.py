from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user, logout_user

from app.extensions import db
from app.models.users import UserData
from app.services.account_service import AccountService
from app.services.follow_service import FollowService
from app.decorators import verified_user

# Blueprint for account-related routes
account_bp = Blueprint("account", __name__)

# ----------------- Explore Accounts -----------------
@account_bp.route("/exploreAccounts/<int:id>/<string:state>")
@login_required
def explore_accounts(id, state):
    user = db.session.get(UserData, id)

    if state == "random":
        accounts = AccountService.random_accounts()

    elif state == "following":
        accounts = AccountService.following_accounts(user)

    elif state == "followers":
        accounts = AccountService.follower_accounts(user)

    else:
        accounts = AccountService.search_accounts(state)

    following_ids = {f.following_id for f in current_user.following}

    return render_template(
        "exploreAccounts.html",
        accounts=accounts,
        following=following_ids
    )

# ----------------- Follow / Unfollow -----------------
@account_bp.route("/follows/<int:id>/<int:st>", methods=["POST"])
@login_required
@verified_user
def follows(id, st):
    if st == 1:
        FollowService.follow_user(id)
    elif st == 2:
        FollowService.unfollow_user(id)

    follower_count = FollowService.follower_count(id)

    return jsonify({
        "status": "success",
        "follower_id": current_user.id,
        "follower_name": current_user.name,
        "followersCount": follower_count,
    })

# ----------------- Logout -----------------
@account_bp.route("/logout/<int:st>")
@login_required
def logout(st):
    logout_user()
    if st == 1:
        return redirect(url_for("main.home"))
    return redirect(url_for("auth.login"))
