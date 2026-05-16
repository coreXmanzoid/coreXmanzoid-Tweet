from app.extensions import db
from app.models.comments import Comments
from app.models.posts import Post
from app.utils.mentions import mentions_parser
from flask_login import current_user
from app.utils.subscription_manager import get_limit, has_feature, is_unlimited


class CommentService:

    @staticmethod
    def add_comment(post_id, content):
        if not has_feature(current_user, "comments", "can_comment"):
            raise ValueError("Your plan does not allow comments.")

        max_length = get_limit(current_user, "comments", "comment_length", 100)
        if not is_unlimited(max_length) and len(content) > int(max_length):
            raise ValueError(f"Comment must be {max_length} characters or fewer for your plan.")

        mentioned_objects = (
            mentions_parser(content)
            if has_feature(current_user, "social", "can_mention")
            else []
        )

        new_comment = Comments(
            content=content,
            post_id=post_id,
            mentions=mentioned_objects,
            user_id=current_user.id,
        )

        db.session.add(new_comment)

        post = db.session.get(Post, post_id)

        if post:
            post.comments += 1

        db.session.commit()

        return new_comment, post

    @staticmethod
    def get_comments(post_id):

        comments = (
            db.session.execute(
                db.select(Comments)
                .where(Comments.post_id == post_id)
                .order_by(Comments.likes.desc())
            )
            .scalars()
            .all()
        )

        return comments

    @staticmethod
    def get_post(post_id):

        return db.session.get(Post, post_id)
