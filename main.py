from flask import Flask, render_template, redirect,  url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, JSON
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import emailHandling
from datetime import datetime
import random, json
data = {"page": "signup",
        "email": "example@gmail.com",
        "usernames": [],
        "emailAlreadyExist": "false",
            }
name, email, username, phone, password, OTP= "", "", "", "", "", ""
posts = None
class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coreXmanzoidTweet.db"


db = SQLAlchemy(model_class=Base)
db.init_app(app)

class UserData(UserMixin, db.Model):
    __tablename__ = "user_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

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
    timestamp: Mapped[str] = mapped_column(String, nullable=False)
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    global name, email, username, password, phone, data, OTP
    if request.method == 'POST':
        if data["page"] == "signup":
            name = request.form.get("name")
            username = request.form.get("username")
            phone = request.form.get("phone")
            email = str(request.form.get("email"))
            password = request.form.get("pin")
            data["email"] = email
            data["page"] = "confirmEmail"
            isUserExist = db.session.execute(db.select(UserData).where((UserData.email == email))).scalar()
            if isUserExist:
                data["page"] = "signup"
                data["emailAlreadyExist"] = "true"
                return render_template('signup.html', data = data)
            OTP = emailHandling.sendEmail(email)
            return render_template('signup.html', data = data)
        elif data['page'] == "confirmEmail":
            userOTP = f'{request.form.get("OTP1")}{request.form.get("OTP2")}{request.form.get("OTP3")}{request.form.get("OTP4")}'
            if emailHandling.checkOTP(OTP, userOTP):
                new_user = UserData(
                    name=name,
                    username=username,
                    email=email,
                    number=phone,
                    password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
                )
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            data["page"] = "signup"
            return redirect(url_for('signup'))
    usernames = db.session.execute(db.select(UserData.username)).scalars().all()
    data["usernames"] = usernames
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

@app.route('/home', methods=['GET', 'POST'])
@login_required
def homepage():
    global posts
    if request.method == 'POST':
        post_content = request.form.get("post-input")
        hashtags = [word for word in post_content.split() if word.startswith('#')]
        post = ' '.join([word for word in post_content.split() if not word.startswith('#')]) 
        datetime_now = datetime.now().isoformat()  # '2025-10-30T14:22:15'
        new_tweet = TweetData(
            content=post,
            hashtags=hashtags,
            user_id=current_user.id,
            timestamp=datetime_now
        )
        db.session.add(new_tweet)
        db.session.commit()
        return redirect(url_for("homepage"))
    
    current_time = datetime.now().isoformat()  # '2025-10-30T14:22:15'
    return render_template('home.html', ct=current_time)


@app.route('/comments/<int:post_id>/<string:content>/<int:state>')
@login_required
def comments(post_id, content, state):
    global posts
    if state == 1:
        new_comment = Comments(
            content = content,
            tweet_id = post_id,
            user_id = current_user.id,
            likes = random.randint(0, 1000)
        )
        db.session.add(new_comment)
        post = db.session.execute(db.select(TweetData).where(TweetData.id == post_id)).scalar()
        post.comments += 1
        db.session.commit()
    comments = db.session.execute(db.select(Comments).where(Comments.tweet_id == post_id).order_by(Comments.id.desc())).scalars().all()
    post = db.session.execute(db.select(TweetData).where(TweetData.id == post_id)).scalar()
    # For GET request → return HTML for comments
    return render_template('comments.html', comments=comments[:15], post=post)

@app.route('/randomPosts/<int:state>/<int:id>', methods=['GET', 'POST'])
def randomPosts(state,id):
    global posts
    if request.method == 'POST':
        update_action = request.get_json()
        for i in range(len(update_action['retweets'])):
            post = db.session.execute(db.select(TweetData).where(TweetData.id == int(update_action['post_id'][i]))).scalar()
            post.likes = update_action['likes'][i]
            post.retweets = update_action['retweets'][i]
            post.shares = update_action['shares'][i]
        db.session.commit()
    if state == 1:
        posts = db.session.execute(db.select(TweetData).where(TweetData.user_id == id).order_by(TweetData.timestamp.desc())).scalars().all()
    else:
        posts = db.session.execute(db.select(TweetData).order_by(TweetData.timestamp.desc())).scalars().all()
    if len(posts) > 10:
        posts = random.sample(posts, 10)
    
    return render_template('posts.html', posts=posts)

@app.route('/exploreAccounts/<int:id>/<string:state>')
def exploreAccounts(id, state):
    user = db.session.get(UserData, id)
    if state == "random":
        accounts = db.session.execute(db.select(UserData).order_by(UserData.id.desc())).scalars().all()
    elif state == "following":
        accounts = [f.following for f in user.following]
    elif state == "followers":
        accounts = [f.follower for f in user.followers]
    else:
        accounts = db.session.execute(db.select(UserData).where(UserData.username.contains(state)).order_by(UserData.id.desc())).scalars().all()
    if len(accounts) > 10:
        accounts = random.sample(accounts, 10)

    following_ids = {f.following_id for f in current_user.following}

    return render_template("exploreAccounts.html",accounts=accounts,following=following_ids)

@app.route("/logout/<int:state>")
@login_required
def logout(state):
    if state == 1:
        logout_user()
        return redirect(url_for('home'))
    logout_user()
    return redirect(url_for('login'))

@app.route("/follows/<int:id>/<int:state>", methods=["GET", "POST"])
def follows(id, state):
    if request.method == "POST":
        if state == 1:
            new_follow = Follow(
                follower_id = current_user.id,
                following_id = id
            )
            db.session.add(new_follow)
            db.session.commit()
        elif state == 2:
            unfollow = db.session.execute(db.select(Follow).where((Follow.follower_id == current_user.id) & (Follow.following_id == id))).scalar()
            db.session.delete(unfollow)
            db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"})

@app.route("/profile/<int:id>")
def profile(id):
    if id == 0:
        return render_template("newPost.html")
    user = db.session.execute(db.select(UserData).where(UserData.id == id)).scalar()
    is_following = False
    is_following = db.session.execute(db.select(Follow).where((Follow.follower_id == current_user.id) & (Follow.following_id == id))).scalar() is not None
    return render_template("profile.html", user=user, is_following=is_following)

if __name__ == "__main__":
    app.run(debug=True)