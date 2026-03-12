from sqlalchemy import func
from app.extensions import db
from app.models.posts import Post
from app.models.users import UserData
from app.models.follows import Follow


class FeedService:

    @staticmethod
    def profile_posts(user_id):
        return (
            db.session.execute(
                db.select(Post)
                .where(Post.user_id == user_id)
                .order_by(Post.timestamp.desc())
            )
            .scalars()
            .all()
        )

    @staticmethod
    def following_posts(user_id):

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

        return (
            db.session.execute(
                db.select(Post)
                .where(Post.user_id.in_(following_ids))
                .order_by(Post.timestamp.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )

    @staticmethod
    def liked_posts(user_id):

        user = db.session.get(UserData, user_id)

        if not user.liked_posts:
            return []

        return (
            db.session.execute(
                db.select(Post)
                .where(Post.id.in_(user.liked_posts))
                .order_by(Post.timestamp.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )

    @staticmethod
    def reposted_posts(user_id):

        user = db.session.get(UserData, user_id)

        if not user.reposted_posts:
            return [], None

        posts = (
            db.session.execute(
                db.select(Post)
                .where(Post.id.in_(user.reposted_posts))
                .order_by(Post.timestamp.desc())
            )
            .scalars()
            .all()
        )

        return posts, user.username

    @staticmethod
    def random_posts():

        return (
            db.session.execute(
                db.select(Post)
                .order_by(func.random())
                .limit(10)
            )
            .scalars()
            .all()
        )
