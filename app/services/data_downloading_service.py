from flask import send_file, jsonify
from app.extensions import db
from app.models.posts import Post
import io, json, zipfile

class DownloadData:

    @staticmethod
    def account_info(user):
        account_information = {
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            "contact": user.contact,
            "profile_picture": user.profile_image_url,
            "account_status" : user.status
        }
        return account_information
    
    @staticmethod
    def user_posts(user):
        posts = db.session.execute(db.select(Post).where(Post.user_id == user.id)).scalars().all()
        user_posts = []
        for i in range(len(posts)):
            post = posts[i]
            post_data = {
                "id" : i + 1,
                "content" : post.content,
                "hashtags": post.hashtags,
                "created_at": post.timestamp.isoformat() if post.timestamp else None,
            }
            user_posts.append(post_data)
        return user_posts
    
    @staticmethod
    def setting_info(user):
        return user.setting
    

    @staticmethod
    def write_zip(account_info, posts, setting_info):
        user_data = {
            "account": account_info,
            "posts": posts,
            "settings": setting_info
        }

        data_file = io.BytesIO()

        with zipfile.ZipFile(data_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("ChatFlick_Data.json", json.dumps(user_data, indent=2, default=str))

        # ✅ move this OUTSIDE the with block
        data_file.seek(0)

        return data_file