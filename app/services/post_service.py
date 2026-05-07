from datetime import timedelta
from app.extensions import db
from app.models.posts import Post
from app.utils.mentions import mentions_parser
from app.utils.time_utils import ensure_utc, utc_now


class PostService:

    @staticmethod
    def _normalize_timestamp(timestamp):
        return ensure_utc(timestamp)

    @staticmethod
    def create_post(content, user_id):

        hashtags = [word for word in content.split() if word.startswith("#")]

        mentions = mentions_parser(content)

        lines = content.split("\n")
        clean_lines = []

        for line in lines:
            clean_words = [
                word for word in line.split() if not word.startswith("#")
            ]
            clean_lines.append(" ".join(clean_words))

        post = "\n".join(clean_lines)

        new_post = Post(
            content=post,
            hashtags=hashtags,
            mentions=mentions,
            user_id=user_id,
        )

        db.session.add(new_post)
        db.session.commit()

        return new_post

    @staticmethod
    def edit_post(post, content):
        post.content = content
        db.session.commit()

    @staticmethod
    def delete_post(post):
        db.session.delete(post)
        db.session.commit()

    @staticmethod
    def can_modify(post, user_id):
        post_timestamp = PostService._normalize_timestamp(post.timestamp)

        return (
            utc_now() - post_timestamp < timedelta(minutes=3)
            and post.user.id == user_id
        )
