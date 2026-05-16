from sqlalchemy import func
from app.extensions import db
from app.models.follows import Follow
from flask_login import current_user
from app.utils.subscription_manager import get_limit, has_feature, is_unlimited


class FollowService:

    @staticmethod
    def follow_user(user_id):
        if not has_feature(current_user, "social", "can_follow"):
            raise ValueError("Your plan does not allow following accounts.")

        existing = db.session.execute(
            db.select(Follow).where(
                (Follow.follower_id == current_user.id)
                & (Follow.following_id == user_id)
            )
        ).scalar()
        if existing:
            return

        max_following = get_limit(current_user, "social", "max_following", 200)
        if not is_unlimited(max_following) and len(current_user.following) >= int(max_following):
            raise ValueError("Following limit reached for your plan.")

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
