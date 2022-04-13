from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

DB_NAME = "dictionary.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "kdlsjfauiog3j2h4g2jkhgekjseghdiuo32498234123213"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None


@app.route("/")
def home():
    return render_template("home.html", logged_in=is_logged_in(), first_name=session.get("firstname"),
                           modify=can_modify())


@app.route("/dictionary/<category>")
def dictionary(category):
    con = create_connection(DB_NAME)
    category = category.strip().title()
    query = "SELECT maori, english, category, level, image, userid, id FROM translation WHERE category IS ? ORDER BY english ASC"
    cur = con.cursor()
    cur.execute(query, (category,))

    translation_list = cur.fetchall()
    con.close()
    if not translation_list:
        return redirect("/dictionary")

    category_list = get_categories()

    return render_template("dictionary.html", logged_in=is_logged_in(), first_name=session.get("firstname"),
                           items=translation_list, categories=category_list, modify=can_modify())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect('/')
    if request.method == "POST":
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        query = """SELECT id, fname, password, can_modify FROM user WHERE email = ?"""
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
            modify = user_data[0][3]
        except IndexError:
            return redirect('/login?error=email+invalid+or+password+incorrect')

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        session['can_modify'] = modify
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in=is_logged_in(), modify=can_modify())


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if is_logged_in():
        return redirect('/')
    if request.method == "POST":
        print(request.form)
        fname = request.form.get("fname").strip().title()
        lname = request.form.get("lname").strip().title()
        email = request.form.get("email").strip().lower()
        password = request.form.get("pass")
        password2 = request.form.get("pass2")
        modify = request.form.get("canmodify")

        if password != password2:
            return redirect('/signup?error=Passwords+dont+match')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DB_NAME)
        query = "INSERT INTO user(id, fname, lname, email, password, can_modify) VALUES(NULL,?,?,?,?,?)"
        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password, modify))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=email+is+already+used')
        con.commit()
        con.close()
        return redirect('/login')

    return render_template("signup.html", logged_in=is_logged_in(), first_name=session.get("firstname"),
                           modify=can_modify())


@app.route("/logout")
def logout():
    if not is_logged_in():
        return redirect("/")
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect("/?message=see+you+next+time")


@app.route("/add", methods=["GET", "POST"])
def add():
    if not can_modify():
        return redirect("/")
    if request.method == "POST":
        maori = request.form.get("maori").strip().lower()
        english = request.form.get("english").strip().lower()
        category = request.form.get("category").strip().title()
        level = request.form.get("level")
        try:
            level = int(level)
        except ValueError:
            return redirect("/add?error=invalid+level")

        con = create_connection(DB_NAME)
        query = "INSERT INTO translation(id, userid, maori, english, category, level) VALUES(NULL,?,?,?,?,?)"
        cur = con.cursor()
        cur.execute(query, (session.get("userid"), maori, english, category, level))
        con.commit()
        con.close()
        return redirect('/dictionary')
    return render_template("adding-data.html", logged_in=is_logged_in(), first_name=session.get("firstname"),
                           modify=can_modify())


@app.route("/delete/<itemid>")
def delete(itemid):
    try:
        itemid = int(itemid)
    except ValueError:
        return redirect(request.referrer + "?error=invalid+item+id")
    if not can_modify():
        return redirect("/")

    con = create_connection(DB_NAME)
    query = "DELETE FROM translation WHERE id=?"
    cur = con.cursor()
    cur.execute(query, (itemid,))
    con.commit()
    con.close()
    return redirect("/dictionary")


@app.route("/dictionary")
def dictionary_all():
    con = create_connection(DB_NAME)
    query = "SELECT maori, english, category, level, image, userid, id FROM translation ORDER BY english ASC"
    cur = con.cursor()
    cur.execute(query)

    translation_list = cur.fetchall()
    con.close()

    category_list = get_categories()
    return render_template("dictionary.html", logged_in=is_logged_in(), first_name=session.get("firstname"),
                           items=translation_list, categories=category_list, modify=can_modify())


def is_logged_in():
    if session.get("email") is None:
        return False
    else:
        return True


def can_modify():
    if session.get("can_modify") == 1:
        return True
    else:
        return False


def get_categories():
    con = create_connection(DB_NAME)
    query = "SELECT category FROM translation"
    cur = con.cursor()
    cur.execute(query)
    category_list = list(set(cur.fetchall()))
    con.close()
    return category_list


def userid_conversion(userid):
    con = create_connection(DB_NAME)
    query = "SELECT fname FROM user where id=?"
    cur = con.cursor()


app.run(host="0.0.0.0")