from flask import Flask, render_template, redirect,  url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String
from werkzeug.security import check_password_hash, generate_password_hash

data = {"page": "signup",
        "email": "example@gmail.com"
            }
class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///coreXmanzoidTweet.db"


db = SQLAlchemy(model_class=Base)
db.init_app(app)

class UserData(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if data["page"] == "signup":
            name = request.form.get("name")
            username = request.form.get("username")
            phone = request.form.get("phone")
            email = str(request.form.get("email"))
            password = request.form.get("pin")
            data["email"] = email
            data["page"] = "confirmEmail"
            return render_template('signup.html', data = data)
        elif data['page'] == "confirmEmail":
            return redirect(url_for('home'))
    return render_template('signup.html', data = data)

if __name__ == "__main__":
    app.run(debug=True)