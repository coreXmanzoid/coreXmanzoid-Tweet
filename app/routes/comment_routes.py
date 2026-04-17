from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from app.decorators import verified_user
from app.services.comment_service import CommentService

comment_bp = Blueprint("comment", __name__)

@comment_bp.route("/comments/<int:post_id>", methods=["GET", "POST"])
@login_required
@verified_user
def comments(post_id):

    data = request.get_json(silent=True) or {}
    state = data.get("state", 0)
    content = data.get("content", "").strip()

    if state == 1:  # add comment

        new_comment, post = CommentService.add_comment(post_id, content)

        comments = CommentService.get_comments(post_id)

        return jsonify({
            'mentions': new_comment.mentions,
            'comment_id': new_comment.id,
            'comments_count': post.comments if post else 0
        })

    comments = CommentService.get_comments(post_id)
    post = CommentService.get_post(post_id)

    return render_template(
        "comments.html",
        comments=comments[:15],
        post=post
    )
