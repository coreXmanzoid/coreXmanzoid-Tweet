import random
from sqlalchemy import func
from app.extensions import db
from app.models.users import UserData
from app.models.follows import Follow


class AccountService:

    @staticmethod
    def random_accounts():
        accounts = (
            db.session.execute(
                db.select(UserData).order_by(func.random()).limit(10)
            )
            .scalars()
            .all()
        )
        return accounts


    @staticmethod
    def following_accounts(user):
        return [f.following for f in user.following]


    @staticmethod
    def follower_accounts(user):
        return [f.follower for f in user.followers]


    @staticmethod
    def search_accounts(query):

        accounts = (
            db.session.execute(
                db.select(UserData)
                .outerjoin(Follow, Follow.following_id == UserData.id)
                .where(UserData.username.contains(query.lower()))
                .group_by(UserData.id)
                .order_by(func.count(Follow.id).desc())
            )
            .scalars()
            .all()
        )

        if len(accounts) > 10:
            accounts = random.sample(accounts, 10)

        return accounts