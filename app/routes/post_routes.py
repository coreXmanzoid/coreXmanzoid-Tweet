from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.post_service import PostService
from app.services.notification_service import NotificationService
from app.extensions import db
from app.services.feed_service import FeedService
from app.services.post_action_service import PostActionService
from flask import render_template
from datetime import datetime, timedelta
from app.models.posts import Post
from app.models.comments import Comments
from app.decorators import verified_user

post_bp = Blueprint("post", __name__)

@post_bp.route("/send-mention-notifications", methods=["POST"])
@login_required
@verified_user
def send_mention_notifications():

    data = request.get_json()

    post_id = data.get("post_id")
    state = data.get("state")

    if state == "post":
        post = db.session.get(Post, post_id)
    else:
        post = db.session.get(Comments, post_id)

    if not post:
        return jsonify({"status": "error", "message": "Post not found"}), 404

    NotificationService.send_mention_notifications(post, state)

    return jsonify({"status": "success"})


@post_bp.route("/managePosts/<int:state>", methods=["POST"])
@login_required
def manage_posts(state):
    data = request.get_json()

    if state == 1:  # create post

        if data.get("user_id") != current_user.id:
            return jsonify({"status": "Unauthorized"}), 403

        content = data.get("content", "").strip()

        if not content:
            return jsonify({"status": "error", "message": "Empty post"}), 400

        post = PostService.create_post(content, current_user.id)

        return jsonify({
            "status": "success",
            "post_id": post.id,
            "username": current_user.username,
            "hashtags": post.hashtags,
            "mentions": post.mentions,
            "timestamp": post.timestamp.isoformat()
        })


    post = db.session.get(Post, data.get("post_id"))

    if not post:
        return jsonify({"status": "Post not found"})


    if not PostService.can_modify(post, current_user.id):
        return jsonify({"status": "Edit timeout or unauthorized access"})


    if state == 2:
        PostService.edit_post(post, data.get("content"))
        return jsonify({"status": "success", "content": post.content})


    if state == 3:
        PostService.delete_post(post)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "Invalid state"})
@post_bp.route("/showPosts/<int:state>/<int:id>")
@login_required
def show_posts(state, id):

    reposts = None

    if state == 1:
        posts = FeedService.profile_posts(id)

    elif state == 2:
        posts = FeedService.following_posts(id)

    elif state == 3:
        posts = FeedService.liked_posts(id)

    elif state == 4:
        posts, reposts = FeedService.reposted_posts(id)

    else:
        posts = FeedService.random_posts()

    return render_template(
        "posts.html",
        posts=posts,
        current_time=datetime.utcnow(),
        timedelta=timedelta,
        reposts=reposts,
    )

@post_bp.route("/PostAction/<int:state>", methods=["POST"])
@login_required
def post_action(state):

    data = request.get_json()
    post_id = data.get("post_id")

    if state == 1:
        post = PostActionService.like_post(post_id, data.get("like"))

    elif state == 2:
        post = PostActionService.repost_post(post_id, data.get("repost"))

    elif state == 3:
        comment = PostActionService.like_comment(post_id, data.get("like"))

        return jsonify({
            "status": "success",
            "likes": comment.likes
        })

    elif state == 4:
        post = PostActionService.share_post(post_id)

        if not post:
            return jsonify({
                "status": "error",
                "message": "Post not found"
            }), 404

        return jsonify({
            "status": "success",
            "shares": post.shares
        })

    return jsonify({
        "current_user_name": current_user.name,
        "likes": post.likes,
        "user_id": post.user_id,
        "reposts": post.reposts,
    })
