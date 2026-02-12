from flask import Flask, render_template, redirect,  url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, JSON, Boolean, Date, DateTime, func
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import emailHandling, random, json, requests, os, re
from datetime import datetime, timedelta
from sqlalchemy.ext.mutable import MutableList
import cloudinary
import cloudinary.uploader
import cloudinary.api
from groq import Groq
from dotenv import load_dotenv
from sqlalchemy.sql import func
load_dotenv()

cloudinary.config(
    cloud_name= os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

data = {"page": "signup",
        "email": "example@gmail.com",
        "emailAlreadyExist": "false",
        }
name, email, username, phone, password, OTP, birth_date="", "", "", "", "", "", ""
user_history = {}  # key: user/session ID, value: list of messages
MAX_HISTORY = 2 
class Base(DeclarativeBase):
    pass


app = Flask(__name__)
# Load API key 
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coreXmanzoidTweet.db"


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
    is_pro_member: Mapped[bool] = mapped_column(Boolean, default=False)
    liked_posts: Mapped[list] = mapped_column(MutableList.as_mutable(JSON),default=list)
    birth_date: Mapped[Date] = mapped_column(Date, nullable=True)
    reposted_posts: Mapped[list] = mapped_column(MutableList.as_mutable(JSON),default=list)

    tweets = relationship("TweetData", back_populates="user")
    comments = relationship("Comments", back_populates="user")

    # USERS WHO FOLLOW THIS USER
    followers: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.following_id",   # <-- important
        back_populates="following",
        cascade="all, delete-orphan"
    )

    # USERS THIS USER IS FOLLOWING
    following: Mapped[list["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",   # <-- important
        back_populates="follower",
        cascade="all, delete-orphan"
    )

class Follow(db.Model):
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # who follows
    follower_id: Mapped[int] = mapped_column(Integer,db.ForeignKey("user_data.id"),nullable=False)

    # who is being followed
    following_id: Mapped[int] = mapped_column(Integer,db.ForeignKey("user_data.id"),nullable=False)

    # user who follows someone
    follower: Mapped["UserData"] = relationship("UserData",foreign_keys=[follower_id],back_populates="following")

    # user who is being followed
    following: Mapped["UserData"] = relationship("UserData",foreign_keys=[following_id],back_populates="followers")

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


with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template("index.html")

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(UserData, user_id)

@app.route('/signup/<int:st>', methods=['GET', 'POST'])
def signup(st):
    global name, email, username, password, phone, data, OTP, birth_date
    if request.method == 'POST':
        if st == 1: #signup form completed
            name = request.form.get("name")
            username = request.form.get("username")
            phone = request.form.get("phone")
            email = str(request.form.get("email"))
            birth_date_str = request.form.get("birthDate")  # "2007-01-11"
            birth_date = (datetime.strptime(birth_date_str, "%Y-%m-%d").date() if birth_date_str else None)
            password = request.form.get("pin")
            
            data["email"] = email
            isUserExist = db.session.execute(db.select(UserData).where((UserData.email == email))).scalar()
            if isUserExist:
                data["page"] = "signup"
                data["emailAlreadyExist"] = "true"
                return render_template('signup.html', data = data)
            data["page"] = "confirmEmail"
            OTP = emailHandling.sendEmail(email)
            if OTP == "0000":
                data["page"] = "signup" #change page if OTP is unsuccessfull
                flash("Failed to send verification email. Please try again.")
            return render_template('signup.html', data = data)
        elif st == 2: #email-verification
            userOTP = f'{request.form.get("OTP1")}{request.form.get("OTP2")}{request.form.get("OTP3")}{request.form.get("OTP4")}'
            if emailHandling.checkOTP(OTP, userOTP):
                new_user = UserData(
                    name=name,
                    username=username,
                    email=email,
                    birth_date=birth_date,
                    number=phone,
                    password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
                )
                db.session.add(new_user)
                db.session.commit()
                data["page"] = "signup"
                return redirect(url_for('login'))
            flash("INVALID OTP")
            data["page"] = "signup"
            return redirect(url_for('signup', st=0))
        elif st == 3: #username verification
            username = request.get_json().get("username")
            isUserExist = db.session.execute(db.select(UserData).where((UserData.username == username))).scalar()
            if isUserExist:
                return jsonify({"status": 'abondonded'})
            return jsonify({"status": 'success'})
    current_date = datetime.now().strftime("%Y-%m-%d")
    data["current_date"] = current_date
    data["page"] = "signup"
    return render_template('signup.html', data = data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = str(request.form.get("username"))
        password = str(request.form.get("pin"))
        if username.endswith('@gmail.com'):
            user = db.session.execute(db.select(UserData).where(UserData.email == username)).scalar()
        else:
            user = db.session.execute(db.select(UserData).where(UserData.username == username)).scalar()
        if not user:
            flash("User doesn't found. Sign in instead.")
            return redirect(url_for('login'))
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('homepage'))
        else:
            flash("Wrong Password Try Again.")
    return render_template('login.html')

@app.route("/update-profile/<int:id>", methods=["POST"])
@login_required
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
        return jsonify({"status": "error", "message": "Unauthorized Access Denied"}), 403
    try:
        result = cloudinary.uploader.upload(
            file,
            folder="profile_pictures",
            public_id=f"user_{id}",
            overwrite=True,
            transformation=[
                {"width": 256, "height": 256, "crop": "fill"},
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )

        image_url = result["secure_url"]
        user.profile_image_url = image_url
        db.session.commit()
        return jsonify({
            "status": "success",
            "image_url": image_url
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/home', methods=['GET', 'POST'])
@login_required
def homepage():
    current_time = datetime.now().isoformat()  # '2025-10-30T14:22:15'
    return render_template('home.html', ct=current_time)

@app.route("/managePosts/<int:state>", methods=['GET', 'POST'])
@login_required
def managePosts(state):
    if request.method == 'POST':
        if state == 1:
            post_content = request.form.get("post-input")
            hashtags = [word for word in post_content.split() if word.startswith('#')]
            post = ' '.join([word for word in post_content.split() if not word.startswith('#')]) 
            datetime_now = datetime.utcnow()  # '2025-10-30T14:22:15'
            new_tweet = TweetData(
                content=post,
                hashtags=hashtags,
                user_id=current_user.id,
                timestamp=datetime_now
            )
            db.session.add(new_tweet)
            db.session.commit()
        elif state == 2:
            data = request.get_json()
            post_id = data.get("post_id")
            post = db.session.get(TweetData, post_id)
            if post:
                if  datetime.utcnow() - post.timestamp < timedelta(minutes=3) and post.user.id==current_user.id:
                    if state == 2: # Update post content
                        new_content = data.get("content")
                        post.content = new_content
                        db.session.commit()
                        return {"status": "success", "content": new_content}
                    elif state == 3: # Delete post
                        db.session.delete(post)
                        db.session.commit()
                        return {"status": "success"}
            return {"status": "Edit timeout or unauthorized Access."}
    return redirect(url_for("homepage"))
    
@app.route('/comments/<int:post_id>/<string:content>/<int:st>')
@login_required
def comments(post_id, content, st):
    if st == 1: # Add new comment
        new_comment = Comments(
            content = content,
            tweet_id = post_id,
            user_id = current_user.id,
        )
        db.session.add(new_comment)
        # fetch the post and update comment count
        post = db.session.execute(db.select(TweetData).where(TweetData.id == post_id)).scalar()
        post.comments += 1
        db.session.commit()
    comments = db.session.execute(db.select(Comments).where(Comments.tweet_id == post_id).order_by(Comments.likes.desc())).scalars().all()
    post = db.session.execute(db.select(TweetData).where(TweetData.id == post_id)).scalar()
    # For GET request → return HTML for comments
    return render_template('comments.html', comments=comments[:15], post=post)

@app.route('/showPosts/<int:state>/<int:id>')
@login_required
def showPosts(state,id):
    posts = []
    reposts = None
    # Get posts for someone profile
    if state == 1:
        posts = db.session.execute(db.select(TweetData).where(TweetData.user_id == id).order_by(TweetData.timestamp.desc())).scalars().all()
    # Get posts for following
    elif state == 2:
        follows = db.session.execute(db.select(Follow).where(Follow.follower_id == id)).scalars().all()
        following_ids = [f.following_id for f in follows]
        if following_ids:
            posts = db.session.execute(db.select(TweetData).where(TweetData.user_id.in_(following_ids)).order_by(TweetData.timestamp.desc()).limit(10)).scalars().all()
    elif state == 3: # Likes
        user = db.session.get(UserData, id)
        liked_post_ids = (user.liked_posts)
        if liked_post_ids:
            posts = db.session.execute(db.select(TweetData).where(TweetData.id.in_(liked_post_ids)).order_by(TweetData.timestamp.desc()).limit(10)).scalars().all()
    elif state == 4: # Reposts
        user = db.session.get(UserData, id)
        reposted_post_ids = (user.reposted_posts)
        if reposted_post_ids:
            reposts = user.username 
            posts = db.session.execute(db.select(TweetData).where(TweetData.id.in_(reposted_post_ids)).order_by(TweetData.timestamp.desc())).scalars().all()
    # Get random posts and Foryou page also refresh route
    else:
        posts = db.session.execute(db.select(TweetData).order_by(func.random()).limit(10)).scalars().all()
    
    current_time = datetime.utcnow()  # '2025-10-30T14:22:15'
    return render_template('posts.html', posts=posts, time_now=current_time, timedelta=timedelta, reposts=reposts)

@app.route('/likePost/<int:state>', methods=['POST'])
@login_required
def post_Action(state):
    data = request.get_json()
    post_id = data.get('post_id')
    if state == 1: # Like action
        post = db.session.get(TweetData, post_id)
        like = data.get('like')
        if like:
            if post_id not in current_user.liked_posts:
                post.likes += 1
                current_user.liked_posts.append(post_id)
        else:
            if post_id in current_user.liked_posts:
                # if the post is already liked then decrease the count by 1 but not less than 0
                post.likes = max(post.likes - 1, 0)
                current_user.liked_posts.remove(post_id)
    elif state == 2: # Repost Action
        post = db.session.get(TweetData, post_id)
        repost = data.get('repost')
        if repost:
            if post_id not in current_user.reposted_posts:
                post.retweets += 1
                current_user.reposted_posts.append(post_id)
        else:
            if post_id in current_user.reposted_posts:
                post.retweets = max(post.retweets - 1, 0)
                current_user.reposted_posts.remove(post_id)
    elif state == 3: # Comment like
        comment = db.session.get(Comments, post_id)
        like = data.get('like')
        if like:
            comment.likes += 1
        else:
            comment.likes = max(comment.likes - 1, 0)
        db.session.commit()
        return jsonify({"status": "success", "likes": comment.likes})
    elif state == 4 : # share post.
        post = db.session.get(TweetData, post_id)
        wasshare = data.get('wasshare')
        if wasshare:
            post.shares += 1
        else:
            post.shares = max(post.shares - 1, 0)
        db.session.commit()
        return jsonify({"status": "success", "shares": post.shares})
    return jsonify({"status": "success", "likes": post.likes, "reposts": post.retweets})

@app.route("/Manzoid-AI", methods=['GET', 'POST'])
@login_required
def manzoid_ai():
    if request.method == 'POST':
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
                max_tokens=180
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

@app.route('/exploreAccounts/<int:id>/<string:state>')
@login_required
def exploreAccounts(id, state):
    user = db.session.get(UserData, id)
    if state == "random":
        accounts = (db.session.execute(db.select(UserData).order_by(func.random()).limit(10)).scalars().all())
    elif state == "following":
        accounts = [f.following for f in user.following]
    elif state == "followers":
        accounts = [f.follower for f in user.followers]
    else: # searching
        accounts = (db.session.execute(
        db.select(UserData).outerjoin(Follow, Follow.following_id == UserData.id)
        .where(UserData.username.contains(state))
        .group_by(UserData.id).order_by(func.count(Follow.id).desc())).scalars().all())
    if len(accounts) > 10:
        accounts = random.sample(accounts, 10)

    following_ids = {f.following_id for f in current_user.following}

    return render_template("exploreAccounts.html",accounts=accounts,following=following_ids)

@app.route("/logout/<int:st>")
@login_required
def logout(st):
    logout_user()
    if st == 1:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route("/follows/<int:id>/<int:st>", methods=["GET", "POST"])
@login_required
def follows(id, st):
    if request.method == "POST":
        if st == 1:
            new_follow = Follow(
                follower_id = current_user.id,
                following_id = id
            )
            db.session.add(new_follow)
            db.session.commit()
        elif st == 2:
            unfollow = db.session.execute(db.select(Follow).where((Follow.follower_id == current_user.id) & (Follow.following_id == id))).scalar()
            db.session.delete(unfollow)
            db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"})

@app.route("/profile/<int:id>")
@login_required
def profile(id):
    if id == 0:
        return render_template("newPost.html")
    user = db.session.execute(db.select(UserData).where(UserData.id == id)).scalar()
    is_following = False
    is_following = db.session.execute(db.select(Follow).where((Follow.follower_id == current_user.id) & (Follow.following_id == id))).scalar() is not None
    return render_template("profile.html", user=user, is_following=is_following)

if __name__ == "__main__":
    app.run(debug=True)