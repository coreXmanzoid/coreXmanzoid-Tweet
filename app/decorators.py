from functools import wraps
from flask_login import current_user


def verified_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if current_user.status != "VERIFIED":
            return "Email not verified. Access Denied.", 403

        return func(*args, **kwargs)

    return wrapper

def pro_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if current_user.status != "PRO":
            return "Pro user required. Access Denied.", 403

        return func(*args, **kwargs)

    return wrapper

def only_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if current_user.username != "hammad":  # Assuming user with ID 1 is the admin
            return "Admin user required. Access Denied.", 403

        return func(*args, **kwargs)

    return wrapper