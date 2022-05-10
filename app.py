from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

DB_NAME = 'smile.db'

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "hj32g4yds87dywqhej23e42378ry32890ey12983yw1h3h12iu3h21381293"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        # connection.execute('pragma foreign keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


@app.route('/')
def home():
    return render_template("home.html", logged_in=is_logged_in())


@app.route('/menu')
def menu():
    con = create_connection(DB_NAME)
    query = "SELECT name, description, volume, price, image, id FROM product"
    cur = con.cursor()
    cur.execute(query)
    product_list = cur.fetchall()
    con.close()
    return render_template("menu.html", products=product_list, logged_in=is_logged_in())


@app.route('/contact')
def contact():
    return render_template("contact.html", logged_in=is_logged_in())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect('/')
    if request.method == "POST":
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        query = """SELECT id, fname, password FROM customer WHERE email = ?"""
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
        except IndexError:
            return redirect('/login?error=email+invalid+or+password+incorrect')

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        print(session)
        return redirect('/')
    return render_template("login.html")


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

        if password != password2:
            return redirect('/signup?error=Passwords+dont+match')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DB_NAME)
        query = "INSERT INTO customer(id, fname, lname, email, password) VALUES(NULL,?,?,?,?)"
        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=email+is+already+used')
        con.commit()
        con.close()
        return redirect('/login')

    return render_template("signup.html", logged_in=is_logged_in())


@app.route('/logout')
def logout():
    if not is_logged_in():
        redirect('/')
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=see+you+next+time')


@app.route('/addtocart/<productid>')
def addtocart(productid):
    if not is_logged_in():
        return redirect('/')

    try:
        productid = int(productid)
    except ValueError:
        return redirect(request.referrer + "?error=invalid+product+id")

    userid = session['userid']
    timestamp = datetime.now()
    print("USer {} would like to add {} to cart".format(userid, productid))

    query = "INSERT into cart(id, userid, productid, timestamp) VALUES (NULL,?,?,?);"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    try:
        cur.execute(query, (userid, productid, timestamp))
    except sqlite3.IntegrityError as e:
        print(e)
        print("### PROBLEM INSERTING INTO DATABASE - FOREIGN KEY ###")
        con.close()
        return redirect(request.referrer + "?error=something+went+wrong")
    con.commit()
    con.close()
    return redirect(request.referrer)


@app.route('/cart')
def cart():
    if not is_logged_in():
        return redirect('/')

    userid = session['userid']
    query = "SELECT productid FROM cart WHERE userid=?;"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (userid,))
    product_ids = cur.fetchall()

    if len(product_ids) == 0:
        return redirect('menu?error=cart+empty')

    for i in range(len(product_ids)):
        product_ids[i] = product_ids[i][0]
    unique_product_ids = list(set(product_ids))
    for i in range(len(unique_product_ids)):
        product_count = product_ids.count(unique_product_ids[i])
        unique_product_ids[i] = [unique_product_ids[i], product_count]

    query = "SELECT name, price FROM product WHERE id = ?;"
    for item in unique_product_ids:
        cur.execute(query, (item[0],))
        item_details = cur.fetchall()
        print(item_details)
        item.append(item_details[0][0])
        item.append(item_details[0][1])

    con.close()
    print(unique_product_ids)

    return render_template('cart.html', cart_data=unique_product_ids, logged_in=is_logged_in())


@app.route('/removefromcart/<productid>')
def remove_from_cart(productid):
    if not is_logged_in():
        return redirect('/')

    customer_id = session['userid']
    query = "DELETE FROM cart WHERE id =(SELECT MIN(id) FROM cart WHERE productid=? and userid = ?);"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (productid, customer_id))
    con.commit()
    con.close()
    return redirect('/cart')


@app.route('/confirmorder')
def confirm_order():
    if not is_logged_in():
        return redirect('/')

    userid = session['userid']
    con = create_connection(DB_NAME)
    cur = con.cursor()
    query = "DELETE FROM cart WHERE userid=?;"
    cur.execute(query, (userid,))
    con.commit()
    con.close()
    return redirect('/checkout')


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not is_logged_in():
        return redirect('/')
    if request.method == "POST":
        return redirect('/scammed')

    return render_template('checkout.html')


@app.route('/scammed')
def scammed():
    return render_template('scammed.html')


def is_logged_in():
    if session.get("email") is None:
        return False
    else:
        return True


app.run(host='0.0.0.0')