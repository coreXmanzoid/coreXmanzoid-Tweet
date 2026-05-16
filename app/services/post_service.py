from datetime import timedelta
from sqlalchemy import func

from app.extensions import db
from app.models.posts import Post
from app.utils.mentions import mentions_parser
from app.utils.subscription_manager import get_limit, has_feature, is_unlimited
from app.utils.time_utils import ensure_utc, utc_now


class PostService:

    @staticmethod
    def _normalize_timestamp(timestamp):
        return ensure_utc(timestamp)

    @staticmethod
    def create_post(content, user_id):
        from app.models.users import UserData

        user = db.session.get(UserData, user_id)
        if not user:
            raise ValueError("User not found")

        max_length = get_limit(user, "posts", "post_length", 180)
        if not is_unlimited(max_length) and len(content) > int(max_length):
            raise ValueError(f"Post must be {max_length} characters or fewer for your plan.")

        posts_per_day = get_limit(user, "posts", "post_per_day", 10)
        if not is_unlimited(posts_per_day):
            day_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
            count = db.session.execute(
                db.select(func.count())
                .select_from(Post)
                .where(Post.user_id == user_id, Post.timestamp >= day_start)
            ).scalar()
            if count >= int(posts_per_day):
                raise ValueError("Daily post limit reached for your plan.")

        hashtags = [word for word in content.split() if word.startswith("#")]
        hashtag_limit = get_limit(user, "posts", "max_hashtags_per_post", 3)
        if not is_unlimited(hashtag_limit) and len(hashtags) > int(hashtag_limit):
            raise ValueError(f"Your plan allows up to {hashtag_limit} hashtags per post.")

        mentions = mentions_parser(content) if has_feature(user, "social", "can_mention") else []

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
        if not PostService.can_edit(post, post.user_id):
            raise ValueError("Your plan does not allow editing this post.")
        content = (content or "").strip()
        max_length = get_limit(post.user, "posts", "post_length", 180)
        if not is_unlimited(max_length) and len(content) > int(max_length):
            raise ValueError(f"Post must be {max_length} characters or fewer for your plan.")
        post.content = content
        db.session.commit()

    @staticmethod
    def delete_post(post, user_id=None):
        if user_id is not None and not PostService.can_delete(post, user_id):
            raise ValueError("Your plan does not allow deleting this post.")
        db.session.delete(post)
        db.session.commit()

    @staticmethod
    def can_modify(post, user_id):
        return PostService.can_edit(post, user_id) or PostService.can_delete(post, user_id)

    @staticmethod
    def _within_window(post, minutes):
        if is_unlimited(minutes):
            return True
        post_timestamp = PostService._normalize_timestamp(post.timestamp)
        return utc_now() - post_timestamp < timedelta(minutes=max(int(minutes or 0), 0))

    @staticmethod
    def can_edit(post, user_id):
        return (
            post.user_id == user_id
            and has_feature(post.user, "posts", "can_edit_post")
            and PostService._within_window(
                post, get_limit(post.user, "posts", "edit_window_minutes", 0)
            )
        )

    @staticmethod
    def can_delete(post, user_id):
        return (
            post.user_id == user_id
            and has_feature(post.user, "posts", "can_delete_post")
            and PostService._within_window(
                post, get_limit(post.user, "posts", "delete_window_minutes", 3)
            )
        )
