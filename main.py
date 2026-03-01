from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, JSON, Boolean, Date, DateTime, func
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    login_required,
    current_user,logout_user,
)
from itsdangerous import BadSignature, BadSignature, SignatureExpired, URLSafeTimedSerializer
import emailHandling, random, json, requests, os
from datetime import datetime, timedelta
from sqlalchemy.ext.mutable import MutableList
import cloudinary
import cloudinary.uploader
import cloudinary.api
from groq import Groq
import firebase_admin
from firebase_admin import credentials, messaging, initialize_app
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)

data = {
    "page": "signup",
    "email": "example@gmail.com",
    "emailAlreadyExist": "false",
}
name, email, username, phone, password, OTP, birth_date = "", "", "", "", "", "", ""
user_history = {}  # key: user/session ID, value: list of messages
MAX_HISTORY = 2


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
# Load API key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coreXmanzoidTweet.db"
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

client = Groq(api_key=GROQ_API_KEY)
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class UserData(UserMixin, db.Model):
    __tablename__ = "user_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    profile_image_url: Mapped[str] = mapped_column(String, nullable=True, default=None)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    Auth_token: Mapped[str] = mapped_column(String, nullable=True, default=None)
    is_pro_member: Mapped[bool] = mapped_column(Boolean, default=False)
    liked_posts: Mapped[list] = mapped_column(MutableList.as_mutable(JSON),default=list)
    birth_date: Mapped[Date] = mapped_column(Date, nullable=True)
    reposted_posts: Mapped[list] = mapped_column(MutableList.as_mutable(JSON),default=list)
    status: Mapped[str] = mapped_column(String, default="Non-Verified")

    tweets = relationship("TweetData", back_populates="user")
    comments = relationship("Comments", back_populates="user")

    received_notifications = relationship(
    "Notification",
    foreign_keys="Notification.recipient_id",
    back_populates="recipient",
    cascade="all, delete-orphan"
    )

    sent_notifications = relationship(
    "Notification",
    foreign_keys="Notification.sender_id",
    back_populates="sender"
    )

    # USERS WHO FOLLOW THIS USER
    followers: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.following_id",  # <-- important
        back_populates="following",
        cascade="all, delete-orphan",
    )

    # USERS THIS USER IS FOLLOWING
    following: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",  # <-- important
        back_populates="follower",
        cascade="all, delete-orphan",
    )


class Notification(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Who receives it
    recipient_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )

    sender_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=True
    )
    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)

    # Type of notification (like, comment, follow, etc.)
    type: Mapped[str] = mapped_column(String(50), nullable=True)

    identifier: Mapped[int] = mapped_column(Integer, nullable=True)  # e.g., post_id or comment_id related to the notification
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    recipient = relationship("UserData", foreign_keys=[recipient_id], back_populates="received_notifications")
    sender = relationship("UserData", foreign_keys=[sender_id], back_populates="sent_notifications")


class Follow(db.Model):
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # who follows
    follower_id: Mapped[int] = mapped_column(Integer,db.ForeignKey("user_data.id"), nullable=False)

    # who is being followed
    following_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey("user_data.id"), nullable=False
    )

    # user who follows someone
    follower: Mapped["UserData"] = relationship(
        "UserData", foreign_keys=[follower_id], back_populates="following"
    )

    # user who is being followed
    following: Mapped["UserData"] = relationship(
        "UserData", foreign_keys=[following_id], back_populates="followers"
    )


class TweetData(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("user_data.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow())
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    retweets: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)

    hashtags: Mapped[JSON] = mapped_column(JSON, default=[])
    mentions: Mapped[JSON] = mapped_column(JSON, default=list)

    user = relationship("UserData", back_populates="tweets")
    comment = relationship("Comments", back_populates="tweet")


class Comments(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    tweet_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("tweet_data.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("user_data.id"), nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    tweet = relationship("TweetData", back_populates="comment")
    user = relationship("UserData", back_populates="comments")

    mentions: Mapped[JSON] = mapped_column(JSON, default=list)

with app.app_context():
    db.create_all()


def init_firebase() -> tuple[bool, str]:
    if firebase_admin._apps:
        return True, "initialized"

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if not service_account_path:
        if os.path.exists("corexmanzoid-twitter-notify-firebase.json"):
            service_account_path = "corexmanzoid-twitter-notify-firebase.json"
        else:
            service_account_path = "firebase-service-account.json"

    if not os.path.exists(service_account_path):
        return False, f"service account file not found: {service_account_path}"

    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
    except Exception as exc:
        return False, f"firebase init failed: {exc}"

    return True, "initialized"


FIREBASE_ENABLED, FIREBASE_STATUS = init_firebase()


@app.context_processor
def inject_runtime_config():
    return {
        "firebase_enabled": FIREBASE_ENABLED,
        "firebase_status": FIREBASE_STATUS,
        "fcm_vapid_key": os.getenv("FCM_VAPID_KEY", ""),
    }


@app.route("/save-token", methods=["POST"])
@login_required
def save_token():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"status": "error", "message": "token is required"}), 400

    current_user.Auth_token = token
    db.session.commit()
    return jsonify({"status": "saved"})


def send_notification(notification: Notification) -> str:
    if not FIREBASE_ENABLED:
        raise RuntimeError(FIREBASE_STATUS)
    token = notification.recipient.Auth_token
    if not token:
        raise ValueError("Missing FCM token")

    message = messaging.Message(
        notification=messaging.Notification(title=notification.title, body=notification.message),
        token=token,
    )
    return messaging.send(message)

@app.route("/check-notifications/<int:user_id>")
@login_required
def check_notifications(user_id):
    notifications = db.session.execute(
        db.select(Notification)
        .where(Notification.recipient_id == user_id)
        .order_by(Notification.created_at.desc())
    ).scalars().all()
    unread_count = sum(1 for n in notifications if not n.is_read)
    return jsonify({"unread_count": unread_count})

@app.route("/send-notification-route/<int:st>/<string:Push>", methods=["POST"])
@login_required
def send_notification_route(st, Push):
    data = request.get_json(silent=True) or {}
    sender_id = data.get("sender_id", current_user.id)
    recipient_id = data.get("recipient_id", None)
    title = data.get("title", "Test Notification")
    message = data.get("message", "This is a test notification from coreXmanzoid.")
    type = data.get("type", "test")
    identifier = data.get("identifier", None)
    if st == 1:  # send notification from anyone to actor (e.g., comment notification)
        new_notification = Notification(
            sender_id=sender_id, 
            recipient_id=recipient_id, 
            title=title,
            message=message, 
            type=type,
            identifier=identifier
        )
        db.session.add(new_notification)
        db.session.commit()
    elif st == 2:  # send notification from actor to all followers
        followers = db.session.execute(
            db.select(Follow).where(Follow.following_id == sender_id)
        ).scalars().all()
        
        notifications = []
        for follow in followers:
            notifications.append(
                Notification(
                    sender_id=sender_id,
                    recipient_id=follow.follower_id,
                    title=title,
                    message=message,
                    type=type,
                    identifier=identifier
                )
            )
        db.session.bulk_save_objects(notifications)
        db.session.commit()
        # db.session.flush()  # flush to get IDs for notifications before sending push notifications
        # if Push == "true":
        #     for notification in notifications:
        #         try:
        #             send_notification(notification)
        #         except Exception as e:
        #             print(f"Failed to send notification: {e}")
        return jsonify({"status": "success", "message": "Notifications save to Database"})
    elif st == 3: # just update database without sending push notification
    # fetch notification from databasae by using type and identifier to send only one notification for same action (e.g., like notification for same post)
        new_notification = db.session.execute(
            db.select(Notification)
            .where(
                (Notification.type == type) &
                (Notification.identifier == identifier)
            )
        ).scalar()
        if new_notification:
            new_notification.created_at = datetime.utcnow()  # update timestamp to show it as new notification
            new_notification.is_read = False  # mark as unread
            new_notification.message = message  # update message in case of any changes
        else:            
            new_notification = Notification(
                sender_id=sender_id, 
                recipient_id=recipient_id,
                title=title,
                message=message, 
                type=type,
                identifier=identifier
            )
            db.session.add(new_notification)
        db.session.commit()
    if Push == "true":
        try:
            send_notification(new_notification)
        except Exception:
            flash("Failed to send test notification.", "error")
        return jsonify({"status": "success", "message": "Notification sent (or queued)"})
    else:
        return jsonify({"status": "success", "message": "Notification saved without push"}), 200

@app.route("/notifications")
@login_required
def notifications():
    notifications = (
        db.session.execute(
            db.select(Notification)
            .where(Notification.recipient_id == current_user.id)
            .order_by(Notification.created_at.desc())
        )
        .scalars()
        .all()
    )
    # keep last 15 notifications and delete rest to optimize database and performance
    if len(notifications) > 15:
        notifications_to_delete = notifications[15:]
        for notification in notifications_to_delete:
            db.session.delete(notification)
    db.session.commit()
    return render_template("notifications.html", notifications=notifications,)

@app.route("/notifications/mark_read/<int:user_id>")
@login_required
@verified_user
def mark_as_read(user_id):
    if user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    db.session.execute(
        db.update(Notification)
        .where(Notification.recipient_id == user_id)
        .values(is_read=True)
    )
    db.session.commit()
    return jsonify({"status": "success"})

@app.route("/")
def home():
    return render_template("index.html")


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(UserData, user_id)

def verified_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.status != "Verified":
            return "Email not verified. Access Denied.", 403
        return func(*args, **kwargs)
    return wrapper

@app.route("/signup/<int:st>", methods=["GET", "POST"])
def signup(st):

    data['current_date'] = datetime.now().strftime("%Y-%m-%d")  # '2025-10-30'
    if request.method == "POST":
        if st == 1: # username verification 
            username = request.get_json().get("username", None) 
            isUserExist = db.session.execute( db.select(UserData).where((UserData.username == username)) ).scalar() 
            if isUserExist: 
                return jsonify({"status": "abondonded"}) 
            return jsonify({"status": "success"}) 
        name = request.form.get("name")
        username = request.form.get("username")
        phone = request.form.get("phone")
        email = request.form.get("email")
        birth_date_str = request.form.get("birthDate")
        password = request.form.get("pin")

        # Convert birth date
        birth_date = (
            datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            if birth_date_str
            else None
        )

        # Check if email already exists
        existing_user = db.session.execute(
            db.select(UserData).where(UserData.email == email)
        ).scalar()

        if existing_user:
            flash("Email already exists.")
            return redirect(url_for('signup', st= 0))

        # Check if username already exists
        existing_username = db.session.execute(
            db.select(UserData).where(UserData.username == username)
        ).scalar()

        if existing_username:
            flash("Username already taken.")
            return redirect(url_for('signup', st= 0))

        # Create new user
        new_user = UserData(
            name=name,
            username=username,
            email=email,
            birth_date=birth_date,
            number=phone,
            password=generate_password_hash(
                password,
                method="pbkdf2:sha256",
                salt_length=8
            ),
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please verify your email.")
        return redirect(url_for("login"))

    return render_template("signup.html", data=data)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = str(request.form.get("username"))
        password = str(request.form.get("pin"))
        if username.endswith("@gmail.com"):
            user = db.session.execute(
                db.select(UserData).where(UserData.email == username)
            ).scalar()
        else:
            user = db.session.execute(
                db.select(UserData).where(UserData.username == username)
            ).scalar()
        if not user:
            flash("User doesn't found. Sign in instead.")
            return redirect(url_for("login"))
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("homepage"))
        else:
            flash("Wrong Password Try Again.")
    return render_template("login.html")

@app.route("/email-verification", methods=["POST"])
@login_required
def email_verification():
    user = current_user

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Generate token
    token = serializer.dumps(
        {"user_id": user.id},
        salt="email-verification-salt"
    )

    verify_link = url_for(
        "verify_email_with_token",
        token=token,
        _external=True
    )

    emailHandling.sendLinkEmail(user.email, verify_link, st=1)

    return jsonify({"status": "success"})

@app.route("/verify-email/<token>")
def verify_email_with_token(token):
    try:
        data = serializer.loads(
            token,
            salt="email-verification-salt",
            max_age=900  # 15 minutes
        )
    except Exception:
        return "Verification link expired or invalid.", 400

    user = db.session.get(UserData, data["user_id"])

    if not user:
        return "User not found.", 404

    if user.status == "Verified":
        return "Email already verified."

    user.status = "Verified"
    db.session.commit()

    return redirect(url_for("homepage"))

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        post_data = request.get_json()
        email = post_data.get("email")
        print(email)
        user = db.session.execute(
            db.select(UserData).where(UserData.email == email)
        ).scalar()

        if user:
            token = serializer.dumps(user.id, salt="password-reset-salt")
            reset_link = url_for("reset_password_with_token", token=token, _external=True)
            emailHandling.sendLinkEmail(email, reset_link, st=2)

        flash("If this email exists, a reset link has been sent.")
        return jsonify({"status": "success", "message": "If this email exists, a reset link has been sent."})

    return render_template("resetPassword.html", data={"page": "resetPassword"})

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_with_token(token):
    try:
        user_id = serializer.loads(token, salt="password-reset-salt", max_age=900)
    except:
        flash("This reset link is invalid or expired.")
        return redirect(url_for("reset_password"))

    user = db.session.get(UserData, user_id)
    if not user:
        flash("Invalid reset link.")
        return redirect(url_for("reset_password"))

    if request.method == "POST":
        post_data = request.get_json(silent=True) or {}
        new_password = post_data.get("newPassword")
        confirm_password = post_data.get("confirmNewPassword")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return render_template("resetPassword.html", data={"page": "newPassword"})

        user.password = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=8)
        db.session.commit()

        flash("Your password has been reset successfully.")
        return jsonify({"status": "success", "message": "Password reset successfully. Please log in with your new password."})

    return render_template("resetPassword.html", data={"page": "newPassword"})

@app.route("/update-profile/<int:id>", methods=["POST"])
@login_required
@verified_user
def upload_profile(id):
    if "profile" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    file = request.files["profile"]

    if file.filename == "":
        return jsonify({"status": "error", "message": "Empty file"}), 400

    user = db.session.get(UserData, id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    if current_user.id != id:
        return (
            jsonify({"status": "error", "message": "Unauthorized Access Denied"}),
            403,
        )
    try:
        result = cloudinary.uploader.upload(
            file,
            folder="profile_pictures",
            public_id=f"user_{id}",
            overwrite=True,
            transformation=[
                {"width": 256, "height": 256, "crop": "fill"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )

        image_url = result["secure_url"]
        user.profile_image_url = image_url
        db.session.commit()
        return jsonify({"status": "success", "image_url": image_url}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/home", methods=["GET", "POST"])
@login_required
def homepage():
    is_user_verified = current_user.status == "Verified"
    current_time = datetime.now().isoformat()  # '2025-10-30T14:22:15'
    return render_template("home.html", ct=current_time, is_user_verified=is_user_verified)

def mentions_parser(content):
    mentioned_usernames = [word[1:] for word in content.split() if word.startswith("@")]
    users = db.session.execute(
        db.select(UserData).where(UserData.username.in_(mentioned_usernames))
    ).scalars().all()

    mentioned_objects = [{"user_id": u.id, "username": u.username} for u in users]
    return mentioned_objects

@app.route("/send-mention-notifications", methods=["POST"])
@login_required
@verified_user
def send_mention_notifications():
    data = request.get_json()
    post_id = data.get("post_id")
    state = data.get("state")
    if state == "post":
        post = db.session.get(TweetData, post_id)
    else: 
        post = db.session.get(Comments, post_id)
    if not post:
        return jsonify({"status": "error", "message": "Post not found"}), 404

    mentioned_objects = post.mentions
    notifications = []
    # create Notification objects
    for obj in mentioned_objects:
        notif = Notification(
            sender_id=post.user.id,
            recipient_id=obj["user_id"],
            title="Mentioned",
            message=f"{post.user.name} mentioned you in a {state}.",
            type=f"mention_{state}",
            identifier=post.id,
        )
        db.session.add(notif)
        notifications.append(notif)

    db.session.flush()
    for notif in notifications:
        try:
            send_notification(notif)
            print("notification send")
        except Exception as e:
            print(f"Failed to send notification: {e}")
    # Commit all notifications at once
    db.session.commit()
    return jsonify({"status": "success", "message": "Mention notifications sent"}), 200
@app.route("/managePosts/<int:state>", methods=["GET", "POST"])
@login_required
@verified_user
def managePosts(state):
    if request.method == "POST":
        if state == 1:
            data = request.get_json()
            if data.get("user_id") != current_user.id:
                return jsonify({"status": "Unauthorized Access Denied"}), 403
            post_content = data.get("content", "")
            if not post_content or not post_content.strip():
                return jsonify({"status": "error", "message": "Empty post"}), 400
            hashtags = [word for word in post_content.split() if word.startswith("#")]
            mentioned_objects = mentions_parser(post_content)

            # Preserve newlines while removing hashtags
            lines = post_content.split("\n")
            clean_lines = []
            for line in lines:
                # Remove hashtags from each line
                clean_words = [word for word in line.split() if not word.startswith("#")]
                clean_lines.append(" ".join(clean_words))

            post = "\n".join(clean_lines)  # keeps original line breaks
            datetime_now = datetime.utcnow()  # '2025-10-30T14:22:15'
            new_tweet = TweetData(
                content=post,
                hashtags=hashtags,
                mentions=mentioned_objects,
                user_id= current_user.id,
                timestamp=datetime_now,
            )
            db.session.add(new_tweet)
            db.session.commit()
            return jsonify({"status": "success", "post_id": new_tweet.id, "username": current_user.username})
        elif state in [2, 3]:  # Edit or delete post
            data = request.get_json()
            post_id = data.get("post_id")
            post = db.session.get(TweetData, post_id)
            if post:
                if (datetime.utcnow() - post.timestamp < timedelta(minutes=3) and post.user.id == current_user.id):
                    if state == 2:  # Update post content
                        new_content = data.get("content")
                        post.content = new_content
                        db.session.commit()
                        return jsonify({"status": "success", "content": new_content})
                    elif state == 3:  # Delete post
                        db.session.delete(post)
                        db.session.commit()
                        return jsonify({"status": "success"})
            return jsonify({"status": "Edit timeout or unauthorized Access."})
    return jsonify({"status": "failed"})


@app.route("/comments/<int:post_id>", methods=["GET", "POST"])
@login_required
@verified_user
def comments(post_id):
    data = request.get_json(silent=True) or {}
    st = data.get("state", 0)
    content = data.get("content", "").strip()
    if st == 1:  # Add new comment
        mentioned_objects  = mentions_parser(content)
        new_comment = Comments(
            content=content,
            tweet_id=post_id,
            mentions=mentioned_objects,
            user_id=current_user.id,
        )
        db.session.add(new_comment)
        # fetch the post and update comment count
        post = db.session.execute(
            db.select(TweetData).where(TweetData.id == post_id)
        ).scalar()
        post.comments += 1
        db.session.commit()
        comments = (
        db.session.execute(
            db.select(Comments)
            .where(Comments.tweet_id == post_id)
            .order_by(Comments.likes.desc())
        )
        .scalars()
        .all()
        )
        return render_template("comments.html", comments=comments[:15], post=post, comment_id=new_comment.id)
    db.session.commit()
    comments = (
        db.session.execute(
            db.select(Comments)
            .where(Comments.tweet_id == post_id)
            .order_by(Comments.likes.desc())
        )
        .scalars()
        .all()
        )
    post = db.session.execute(
        db.select(TweetData).where(TweetData.id == post_id)
    ).scalar()
    # For GET request → return HTML for comments
    return render_template("comments.html", comments=comments[:15], post=post)


@app.route("/showPosts/<int:state>/<int:id>")
@login_required
def showPosts(state, id):
    posts = []
    reposts = None
    # Get posts for someone profile
    if state == 1:
        posts = (
            db.session.execute(
                db.select(TweetData)
                .where(TweetData.user_id == id)
                .order_by(TweetData.timestamp.desc())
            )
            .scalars()
            .all()
        )
    # Get posts for following
    elif state == 2:
        follows = (
            db.session.execute(db.select(Follow).where(Follow.follower_id == id))
            .scalars()
            .all()
        )
        following_ids = [f.following_id for f in follows]
        if following_ids:
            posts = (
                db.session.execute(
                    db.select(TweetData)
                    .where(TweetData.user_id.in_(following_ids))
                    .order_by(TweetData.timestamp.desc())
                    .limit(10)
                )
                .scalars()
                .all()
            )
    elif state == 3:  # Likes
        user = db.session.get(UserData, id)
        liked_post_ids = user.liked_posts
        if liked_post_ids:
            posts = (
                db.session.execute(
                    db.select(TweetData)
                    .where(TweetData.id.in_(liked_post_ids))
                    .order_by(TweetData.timestamp.desc())
                    .limit(10)
                )
                .scalars()
                .all()
            )
    elif state == 4:  # Reposts
        user = db.session.get(UserData, id)
        reposted_post_ids = user.reposted_posts
        if reposted_post_ids:
            reposts = user.username
            posts = (
                db.session.execute(
                    db.select(TweetData)
                    .where(TweetData.id.in_(reposted_post_ids))
                    .order_by(TweetData.timestamp.desc())
                )
                .scalars()
                .all()
            )
    # Get random posts and Foryou page also refresh route
    else:
        posts = (
            db.session.execute(db.select(TweetData).order_by(func.random()).limit(10))
            .scalars()
            .all()
        )

    current_time = datetime.utcnow()  # '2025-10-30T14:22:15'
    return render_template(
        "posts.html",
        posts=posts,
        time_now=current_time,
        timedelta=timedelta,
        reposts=reposts,
    )


@app.route("/likePost/<int:state>", methods=["POST"])
@login_required
@verified_user
def post_Action(state):
    data = request.get_json()
    post_id = data.get("post_id")
    if state == 1:  # Like action
        post = db.session.get(TweetData, post_id)
        like = data.get("like")
        if like:
            if post_id not in current_user.liked_posts:
                post.likes += 1
                current_user.liked_posts.append(post_id)
        else:
            if post_id in current_user.liked_posts:
                # if the post is already liked then decrease the count by 1 but not less than 0
                post.likes = max(post.likes - 1, 0)
                current_user.liked_posts.remove(post_id)
        db.session.commit()
    elif state == 2:  # Repost Action
        post = db.session.get(TweetData, post_id)
        repost = data.get("repost")
        if repost:
            if post_id not in current_user.reposted_posts:
                post.retweets += 1
                current_user.reposted_posts.append(post_id)
        else:
            if post_id in current_user.reposted_posts:
                post.retweets = max(post.retweets - 1, 0)
                current_user.reposted_posts.remove(post_id)
        db.session.commit()
    elif state == 3:  # Comment like
        comment = db.session.get(Comments, post_id)
        like = data.get("like")
        if like:
            comment.likes += 1
        else:
            comment.likes = max(comment.likes - 1, 0)
        db.session.commit()
        return jsonify({"status": "success", "likes": comment.likes})
    elif state == 4:  # share post.
        post = db.session.get(TweetData, post_id)
        wasshare = data.get("wasshare")
        if wasshare:
            post.shares += 1
        else:
            post.shares = max(post.shares - 1, 0)
        db.session.commit()
        return jsonify({"status": "success", "shares": post.shares})
    return jsonify({"current_user_name": current_user.name, "likes": post.likes, "user_id": post.user_id, "reposts": post.retweets})


@app.route("/Manzoid-AI", methods=["GET", "POST"])
@login_required
@verified_user
def manzoid_ai():
    if request.method == "POST":
        data = request.get_json()

        if not data or "message" not in data or "user_id" not in data:
            return jsonify({"error": "Message and user_id are required"}), 400

        user_id = data["user_id"]
        new_message = data["message"].strip()

        if not new_message:
            return jsonify({"error": "Empty message"}), 400
        if len(new_message) > 130:
            return jsonify({"error": "Message too long"}), 400

        # Get user's previous messages, default to empty list
        history = user_history.get(user_id, [])

        # Construct context prompt
        context_prompt = ""
        for i, (user_msg, ai_reply) in enumerate(history):
            context_prompt += f"User: {user_msg}\nAI: {ai_reply}\n"

        # Add the new user message
        context_prompt += f"User: {new_message}\nAI:"

        try:
            # Call Llama 3 API
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": context_prompt}],
                max_tokens=180,
            )

            answer = response.choices[0].message.content.strip()

            # Update history for this user
            history.append((new_message, answer))
            if len(history) > MAX_HISTORY:
                history = history[-MAX_HISTORY:]  # keep only last N messages
            user_history[user_id] = history

            return jsonify({"reply": answer})

        except Exception as e:
            print("Groq error:", e)
            return jsonify({"error": "AI service unavailable"}), 503
    else:
        return render_template("AI.html")


# @app.route("/api/ai/chat", methods=["POST"])
# def ai_chat():
#     data = request.get_json()

#     if not data or "message" not in data:
#         return jsonify({"error": "Message is required"}), 400

#     prompt = data["message"].strip()

#     if not prompt:
#         return jsonify({"error": "Empty message"}), 400

#     if len(prompt) > 100:
#         return jsonify({"error": "Message too long"}), 400

#     try:
#         response = client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=150
#         )

#         answer = response.choices[0].message.content
#         return jsonify({"reply": answer})

#     except Exception as e:
#         print("Groq error:", e)
#         return jsonify({"error": "AI service unavailable"}), 503


@app.route("/exploreAccounts/<int:id>/<string:state>")
@login_required
def exploreAccounts(id, state):
    user = db.session.get(UserData, id)
    if state == "random":
        accounts = (
            db.session.execute(db.select(UserData).order_by(func.random()).limit(10))
            .scalars()
            .all()
        )
    elif state == "following":
        accounts = [f.following for f in user.following]
    elif state == "followers":
        accounts = [f.follower for f in user.followers]
    else:  # searching
        accounts = (
            db.session.execute(
                db.select(UserData)
                .outerjoin(Follow, Follow.following_id == UserData.id)
                .where(UserData.username.contains(state))
                .group_by(UserData.id)
                .order_by(func.count(Follow.id).desc())
            )
            .scalars()
            .all()
        )
    if len(accounts) > 10:
        accounts = random.sample(accounts, 10)

    following_ids = {f.following_id for f in current_user.following}

    return render_template(
        "exploreAccounts.html", accounts=accounts, following=following_ids
    )


@app.route("/logout/<int:st>")
@login_required
def logout(st):
    logout_user()
    if st == 1:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/follows/<int:id>/<int:st>", methods=["GET", "POST"])
@login_required
@verified_user
def follows(id, st):
    if request.method == "POST":
        if st == 1:
            new_follow = Follow(follower_id=current_user.id, following_id=id)
            db.session.add(new_follow)
            db.session.commit()
        elif st == 2:
            unfollow = db.session.execute(
                db.select(Follow).where(
                    (Follow.follower_id == current_user.id)
                    & (Follow.following_id == id)
                )
            ).scalar()
            db.session.delete(unfollow)
            db.session.commit()
        follower_count = db.session.execute(
            db.select(func.count(Follow.id)).where(Follow.following_id == id)
        ).scalar()
        return jsonify({"status": "success", "follower_id": current_user.id, "follower_name": current_user.name, "followersCount": follower_count})
    return jsonify({"status": "failed"})


@app.route("/profile/<int:id>")
@login_required
def profile(id):
    if id == 0:
        return render_template("newPost.html")
    user = db.session.execute(db.select(UserData).where(UserData.id == id)).scalar()
    is_following = False
    is_following = (
        db.session.execute(
            db.select(Follow).where(
                (Follow.follower_id == current_user.id) & (Follow.following_id == id)
            )
        ).scalar()
        is not None
    )
    return render_template("profile.html", user=user, is_following=is_following)

if __name__ == "__main__":
    app.run(debug=True)
