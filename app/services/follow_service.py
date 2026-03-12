from sqlalchemy import func
from app.extensions import db
from app.models.follows import Follow
from flask_login import current_user


class FollowService:

    @staticmethod
    def follow_user(user_id):

        new_follow = Follow(
            follower_id=current_user.id,
            following_id=user_id
        )

        db.session.add(new_follow)
        db.session.commit()


    @staticmethod
    def unfollow_user(user_id):

        follow = db.session.execute(
            db.select(Follow).where(
                (Follow.follower_id == current_user.id) &
                (Follow.following_id == user_id)
            )
        ).scalar()

        if follow:
            db.session.delete(follow)
            db.session.commit()


    @staticmethod
    def follower_count(user_id):

        return db.session.execute(
            db.select(func.count(Follow.id))
            .where(Follow.following_id == user_id)
        ).scalar()