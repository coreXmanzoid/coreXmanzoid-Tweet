from app.extensions import login_manager
from app.models.users import UserData
from app.extensions import db


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(UserData, user_id)