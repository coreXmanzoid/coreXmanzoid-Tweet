from flask import Flask, render_template, redirect, url_for, flash, abort, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators, IntegerField, PasswordField, TextAreaField
from wtforms.validators import DataRequired
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import requests, second
from functools import wraps
from datetime import datetime


def only_admin(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return fun(*args, **kwargs)
    return wrapper

# getting team members detail.
url = 'https://api.npoint.io/661ce7396adc94112757'
Name, Email, Age, Password, Number = None, None, None, None, None
# Create signUp form
class signUp(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired(), validators.Length(min=3, max=20, message='invalid Name')])
    age = IntegerField(label='Age' ,validators=[DataRequired()])
    email = StringField(label='Email', validators=[DataRequired(), validators.Email()])
    number = IntegerField(label='Phone Number', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired(), validators.Length(min=8, message='Password should be at least 8 characters long')])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(), validators.EqualTo('password', 'Password miss match' )])
    submit = SubmitField(label='Sign Up')
    
class ConfirmEmail(FlaskForm):
    otp = IntegerField(label='', validators=[DataRequired()])
    confirm = SubmitField('Confirm OTP')
    
class LoginForm(FlaskForm):
      user_email = StringField(label='Email', validators=[DataRequired(), validators.Email('Please enter a valid Email.')])
      user_password = PasswordField(label='Password', validators=[DataRequired(), validators.Length(min=8, message='Password should be at least 8 characters long')])
      login = SubmitField('Login')
      
class SendMail(FlaskForm):
    message = TextAreaField(label='Message', validators=[DataRequired()])    
    send = SubmitField('Send Message')
      
class Base(DeclarativeBase):
    pass

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///CoreXManzoid.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)
bootstrap = Bootstrap5(app)
email = second.EmailHandling()


class UserDB(UserMixin, db.Model):
    __tablename__ = 'User'
    id: Mapped[int] = mapped_column(Integer, unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=True)
    
    questions = relationship("UserComment", back_populates="user")

class  UserComment(db.Model):
    __tablename__ = 'Questions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('User.id'))
    answer: Mapped[str] = mapped_column(String, nullable=True)
    user = relationship("UserDB", back_populates='questions')
    
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(UserDB, user_id)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    response = requests.get(url)
    response.raise_for_status()
    details = response.json()['details']
    return render_template('about.html', team=details)

@app.route('/about/<int:memberid>')
def memberdetails(memberid):
    response = requests.get(url)
    details = response.json()
    details = details['details']
    data_required = None
    for data in details:
        if data['id'] == memberid:
            data_required = [data['Details'], data['name'], data['cv']]
    return render_template('memberdetails.html', detail= data_required)

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = signUp()
    if form.validate_on_submit():
        global Name, Age, Email, Number, Password
        Name= form.name.data
        Age=form.age.data
        Email=form.email.data
        Number=form.number.data
        Password=form.password.data
        user_exist = db.session.execute(db.select(UserDB).where(Email == UserDB.email)).scalar()
        if user_exist:
            flash('Email already registered. Please login instead.')
            return redirect(url_for('login'))
        email.send_email(userEmail=Email)
        return redirect(url_for('confirm_email'))   
    return render_template('signUp.html', form=form)

@app.route('/confirmEmail', methods=['GET', 'POST'])
def confirm_email():
    confirmform = ConfirmEmail()
    if confirmform.validate_on_submit():
        is_verified = email.checkOTP(userOTP= str(confirmform.otp.data))
        if is_verified:
            Salted_and_Hashed_Password = generate_password_hash(Password,method='pbkdf2:sha256', salt_length=8)
            new_user = UserDB(
                name= Name,
                age=Age,
                email=Email,
                number=Number,
                password=Salted_and_Hashed_Password,
                status="Pending"
            )
            db.session.add(new_user)
            db.session.commit()
            return render_template('confirmEmail.html', Emailconfirm=1)
        else:
            return render_template('confirmEmail.html', Emailconfirm=2)
    return render_template('confirmEmail.html', email=Email, form=confirmform)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_email = form.user_email.data
        user_password = form.user_password.data
        user_data = db.session.execute(db.select(UserDB).where(UserDB.email == user_email)).scalar()
        if not user_data:
            flash('Please Enter a correct Email.')
            return redirect(url_for('login'))
        if not check_password_hash(user_data.password, user_password):
            flash('Please Enter a correct Password')
            return redirect(url_for('login'))
        login_user(user_data)
        return redirect(url_for('front_page', name=current_user.name))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))   
@app.route('/<string:name>/User-Page', methods=['GET', 'POST'])
@login_required
def user_page(name):
    form = SendMail()
    if form.validate_on_submit():
        new_commment = UserComment(
            text = form.message.data,
            date = datetime.now(),
            user_id = current_user.id,
            answer = 'Answer Unavailable',
        )
        db.session.add(new_commment)
        db.session.commit()
        return redirect(url_for('front_page', name=current_user.name))
    return render_template('loggedin.html', name=name, form=form, account_status=str(current_user.status))

@app.route('/<string:name>/front-Page', methods=['GET', 'POST'])
@login_required
def front_page(name):
    with app.app_context():
        comments = db.session.execute(db.select(UserComment).where(UserComment.user_id == current_user.id)).scalars().all()
        if name == 'show older messages':
            return render_template('loggingin.html', name = current_user.name , comments =comments[::-1][3:])
        return render_template('loggingin.html', name = name, comments =comments[::-1][:3])

@app.route('/verification/<string:status>', methods=['GET', 'POST'])    
@login_required
@only_admin
def verify(status):
    with app.app_context():
        if status == "Pending":
            user_data = db.session.execute(db.select(UserDB).where(UserDB.status == 'Pending')).scalars().all()
            if len(user_data) == 0:
                return '<h1>No Pending Verification.</h1><p>Have a rest.</p>'
            if request.method == 'POST':
                updated_account_status = request.form.getlist('status')
                for i in range(len(user_data)):
                    user_data[i].status = updated_account_status[i]
                    print(updated_account_status[i])
                db.session.commit()
                return redirect(url_for('verify', status='Pending'))
        elif status == "Active":
            user_data = db.session.execute(db.select(UserDB).where(UserDB.status == 'Active')).scalars().all()
            if len(user_data) == 0:
                return '<h1>There is no verified account.</h1><p>Go to <a>/verification/Pending</a> to start verification.</p>'
            if request.method == 'POST':
                updated_account_status = request.form.getlist('status')
                for i in range(len(user_data)):
                    user_data[i].status = updated_account_status[i]
                db.session.commit()
                return redirect(url_for('verify', status='Pending'))
        else: 
            user_data = None
        return render_template('verification.html', users= user_data)
    
@app.route('/Answer/<int:id>', methods=['GET', 'POST'])
@login_required
@only_admin
def answer(id):
    with app.app_context():
        comments = db.session.execute(db.select(UserComment).where(UserComment.answer == 'Answer Unavailable')).scalars().all()
        if request.method == 'POST':
            comment = db.session.execute(db.select(UserComment).where(UserComment.id == id)).scalar()
            admin_answer = str(request.form.get('answer'))
            if len(admin_answer) != 0:
                comment.answer = request.form.get('answer')
            else:
                comment.answer = 'Answer Unavailable'
            db.session.commit()
            return redirect(url_for('answer', id=1))
        return render_template('answer.html', comments=comments)
if __name__ == '__main__':
    app.run(debug=True)

