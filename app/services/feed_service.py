from sqlalchemy import func, or_
from app.extensions import db
from app.models.posts import Post
from app.models.users import UserData
from app.models.follows import Follow


class FeedService:

    @staticmethod
    def _with_exclusions(query, exclude_ids):
        if exclude_ids:
            query = query.where(Post.id.notin_(exclude_ids))
        return query

    @staticmethod
    def _visible_posts(query):
        return query.where(or_(Post.status.is_(None), Post.status == "ACTIVE"))

    @staticmethod
    def profile_posts(user_id, limit=None, exclude_ids=None):
        query = (
            db.select(Post)
            .where(Post.user_id == user_id)
            .order_by(Post.timestamp.desc())
        )
        query = FeedService._visible_posts(query)
        query = FeedService._with_exclusions(query, exclude_ids)
        if limit:
            query = query.limit(limit)

        return (
            db.session.execute(query)
            .scalars()
            .all()
        )

    @staticmethod
    def following_posts(user_id, limit=None, exclude_ids=None):

        follows = (
            db.session.execute(
                db.select(Follow).where(Follow.follower_id == user_id)
            )
            .scalars()
            .all()
        )

        following_ids = [f.following_id for f in follows]

        if not following_ids:
            return []

        query = (
            db.select(Post)
            .where(Post.user_id.in_(following_ids))
            .order_by(Post.timestamp.desc())
        )
        query = FeedService._visible_posts(query)
        query = FeedService._with_exclusions(query, exclude_ids)
        if limit:
            query = query.limit(limit)

        return (
            db.session.execute(query)
            .scalars()
            .all()
        )

    @staticmethod
    def liked_posts(user_id, limit=None, exclude_ids=None):

        user = db.session.get(UserData, user_id)

        if not user.liked_posts:
            return []

        query = (
            db.select(Post)
            .where(Post.id.in_(user.liked_posts))
            .order_by(Post.timestamp.desc())
        )
        query = FeedService._visible_posts(query)
        query = FeedService._with_exclusions(query, exclude_ids)
        if limit:
            query = query.limit(limit)

        return (
            db.session.execute(query)
            .scalars()
            .all()
        )

    @staticmethod
    def reposted_posts(user_id, limit=None, exclude_ids=None):

        user = db.session.get(UserData, user_id)

        if not user.reposted_posts:
            return [], None

        query = (
            db.select(Post)
            .where(Post.id.in_(user.reposted_posts))
            .order_by(Post.timestamp.desc())
        )
        query = FeedService._visible_posts(query)
        query = FeedService._with_exclusions(query, exclude_ids)
        if limit:
            query = query.limit(limit)

        posts = (
            db.session.execute(query)
            .scalars()
            .all()
        )

        return posts, user.username

    @staticmethod
    def random_posts(limit=None, exclude_ids=None):
        query = FeedService._visible_posts(db.select(Post).order_by(func.random()))
        query = FeedService._with_exclusions(query, exclude_ids)
        if limit:
            query = query.limit(limit)

        return (
            db.session.execute(query)
            .scalars()
            .all()
        )
