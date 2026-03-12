from app.extensions import db
from flask_login import current_user
from app.models.posts import Post
from app.models.comments import Comments


class PostActionService:

    @staticmethod
    def like_post(post_id, like):

        post = db.session.get(Post, post_id)

        if like:
            if post_id not in current_user.liked_posts:
                post.likes += 1
                current_user.liked_posts.append(post_id)

        else:
            if post_id in current_user.liked_posts:
                post.likes = max(post.likes - 1, 0)
                current_user.liked_posts.remove(post_id)

        db.session.commit()

        return post


    @staticmethod
    def repost_post(post_id, repost):

        post = db.session.get(Post, post_id)

        if repost:
            if post_id not in current_user.reposted_posts:
                post.reposts += 1
                current_user.reposted_posts.append(post_id)

        else:
            if post_id in current_user.reposted_posts:
                post.reposts = max(post.reposts - 1, 0)
                current_user.reposted_posts.remove(post_id)

        db.session.commit()

        return post


    @staticmethod
    def like_comment(comment_id, like):

        comment = db.session.get(Comments, comment_id)

        if like:
            comment.likes += 1
        else:
            comment.likes = max(comment.likes - 1, 0)

        db.session.commit()

        return comment


    @staticmethod
    def share_post(post_id, share):

        post = db.session.get(Post, post_id)

        if share:
            post.shares += 1
        else:
            post.shares = max(post.shares - 1, 0)

        db.session.commit()

        return post
