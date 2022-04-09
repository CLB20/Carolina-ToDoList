import itsdangerous
import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, ListForm, TaskForm

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
Bootstrap(app)

# Connect to DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Configure tables

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    lists = db.relationship("List", backref="owner")
    tasks = db.relationship("Task", backref="owner")


class List(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    tasks = db.relationship("Task", backref="parent")


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("lists.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash("This email is already registered. Log in instead.")
            return redirect(url_for("login"))
        password = generate_password_hash(form.password.data,
                                          method="pbkdf2:sha256",
                                          salt_length=8)
        new_user = User(email=form.email.data,
                        password=password,
                        name=form.name.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("lists"))

    return render_template("login.html", form=form, title="Register")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("The email doesn't exist. Please try again.")
            redirect(url_for("login"))
        elif not check_password_hash(user.password, form.password.data):
            flash("Incorrect password. Please try again")
            redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("lists"))

    return render_template("login.html", form=form, title="Sign In")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/lists", methods=["GET", "POST"])
@login_required
def lists():
    form = ListForm()
    user = current_user.id
    user_lists = List.query.filter_by(user_id=user)
    if form.validate_on_submit():
        list_name = form.list_name.data
        existing_list = List.query.filter_by(list_name=list_name, user_id=user).first()
        if not existing_list:
            new_list = List(list_name=list_name,
                            user_id=user)
            db.session.add(new_list)
            db.session.commit()
            return redirect(url_for("lists"))
        flash("You already have a list with this name. Go to the list instead.")
        return redirect(url_for("lists"))

    return render_template("lists.html", form=form, title="Your Lists", lists=user_lists)


@app.route("/delete/list/<int:list_id>")
@login_required
def delete_list(list_id):
    list_to_delete = List.query.get(list_id)
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for("lists"))


@app.route("/list/<int:list_id>", methods=["GET", "POST"])
@login_required
def list_tasks(list_id):
    user = current_user.id
    list_name = List.query.get(list_id).list_name
    tasks = Task.query.filter_by(list_id=list_id)
    form = TaskForm()
    if form.validate_on_submit():
        new_task = Task(task=form.task.data,
                        list_id=list_id,
                        user_id=user)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("list_tasks", list_id=list_id))

    return render_template("list.html", form=form, tasks=tasks, title=list_name)


@app.route("/delete_task/<int:task_id>")
@login_required
def delete_task(task_id):
    task_to_delete = Task.query.get(task_id)
    list_id = task_to_delete.list_id
    owner = task_to_delete.user_id
    if current_user.id == owner:
        db.session.delete(task_to_delete)
        db.session.commit()
    else:
        return redirect(url_for("home"))
    return redirect(url_for("list_tasks", list_id=list_id))


@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task_to_edit = Task.query.get(task_id)
    owner = task_to_edit.user_id
    if current_user.id == owner:
        list_id = task_to_edit.list_id
        list_name = List.query.get(list_id).list_name
        tasks = Task.query.filter_by(list_id=list_id)
        form = TaskForm(task=task_to_edit.task)
        if form.validate_on_submit():
            task_to_edit.task = form.task.data
            db.session.commit()
            return redirect(url_for("list_tasks", list_id=list_id))
        return render_template("list.html", form=form, tasks=tasks, title=list_name)

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
