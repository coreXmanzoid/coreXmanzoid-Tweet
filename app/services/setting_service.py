from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.support_requests import Support
from app.models.report import Report
from app.models.posts import Post
from app.models.follows import Follow
class SettingService:

    @staticmethod
    def change_name(user, new_name):
        user.name = new_name
        db.session.commit()

    
    @staticmethod
    def change_username(user, new_username):
        user.username = new_username.lower()
        db.session.commit()

    @staticmethod
    def change_contact(user, new_contact):
        user.contact = new_contact
        db.session.commit()

    @staticmethod
    def change_bio(user, new_bio):
        user.set_setting("profile-info", "bio", new_bio)
        db.session.commit()

    @staticmethod
    def change_website(user, new_website):
        user.set_setting("account-info", "website", new_website)
        db.session.commit()

    @staticmethod
    def change_about(user, new_about):
        user.set_setting("account-info", "about", new_about)
        db.session.commit()

    @staticmethod
    def change_email(user, new_email):
        user.status = "UNVERIFIED"
        user.email = new_email.lower()
        db.session.commit()
   
    @staticmethod
    def change_birthdate(user, new_birthdate):
        user.birth_date = new_birthdate
        db.session.commit()

    @staticmethod
    def verify_password_change(user, old_password, new_password_01, new_password_02):
        user_password = user.password 
        if new_password_01 == new_password_02:
            if check_password_hash(user_password, old_password):
                return True
        return False
    
    @staticmethod
    def change_password(user, new_password):
        hash_password = generate_password_hash(password=new_password, method='pbkdf2:sha256', salt_length=8)
        user.password = hash_password
        db.session.commit()

    @staticmethod
    def change_privacy_status(user, privacy_status):
        user.set_setting("privacy-setting", "private_account", privacy_status)
        db.session.commit()

    @staticmethod
    def change_birthdate_status(user, birthdate_status):
        user.set_setting("privacy-setting", "show_birthdate", birthdate_status)
        db.session.commit()

    @staticmethod
    def change_bio_status(user, bio_status):
        user.set_setting("privacy-setting", "show_bio", bio_status)
        db.session.commit()

    @staticmethod
    def change_myStatus_status(user, myStatus):
        user.set_setting("privacy-setting", "show_status", myStatus)
        db.session.commit()

    @staticmethod
    def change_theme(user, theme):
        normalized_theme = "light" if theme == "light" else "dark"
        user.set_setting("support", "theme", normalized_theme)
        db.session.commit()

    @staticmethod
    def create_report(user_id, message):
        new_report = Report(
            report_text = message,
            user_id = user_id
        )
        db.session.add(new_report)
        db.session.commit()
    
    @staticmethod
    def create_support_request(user_id, category, message):
        new_problem = Support(
            category= category,
            message = message,
            user_id = user_id
        )
        db.session.add(new_problem)
        db.session.commit()
        
    """Notification Service"""
    
    @staticmethod
    def change_email_notifications(user, status):
        user.set_setting('notifications-setting', 'email_notifications', status)
        db.session.commit()

    @staticmethod
    def change_push_notifications(user, status):
        user.set_setting('notifications-setting', 'push_notifications', status)
        db.session.commit()
        
    @staticmethod
    def change_newFollower_notifications(user, status):
        user.set_setting('notifications-setting', 'new_followers', status)
        db.session.commit()

    @staticmethod
    def change_mentions_notifications(user, status):
        user.set_setting('notifications-setting', 'mentions', status)
        db.session.commit()

    @staticmethod
    def change_likeComments_notifications(user, status):
        user.set_setting('notifications-setting', 'likes_comments', status)
        db.session.commit()
        
    @staticmethod
    def change_reposts_notifications(user, status):
        user.set_setting('notifications-setting', 'reposts', status)
        db.session.commit()


    """Danger Zone"""

    @staticmethod
    def deactivate_account(user):
        user.status = "DEACTIVED"
        db.session.commit()

    @staticmethod
    def delete_account(user):
        db.session.delete(user)
        db.session.commit()
    
