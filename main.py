from flask import Flask, render_template, redirect,  url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import emailHandling
data = {"page": "signup",
        "email": "example@gmail.com",
        "usernames": [],
        "emailAlreadyExist": "false",
            }
name, email, username, phone, password, OTP= "", "", "", "", "", ""
class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coreXmanzoidTweet.db"


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class UserData(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique = True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    tweet = relationship("TweetData", back_populates="user")

class TweetData(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("user_data.id"), nullable=False)

    user = relationship("UserData", back_populates="tweet")

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
    if request.method == 'POST':
        post = request.form.get("post-input")
        new_tweet = TweetData(
            content=post,
            user_id=current_user.id
        )
        db.session.add(new_tweet)
        db.session.commit()
    return render_template('home.html')



if __name__ == "__main__":
    app.run(debug=True)