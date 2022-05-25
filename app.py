from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
import datetime

DB_NAME = "maori_dictionary.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "secret_key"


# creates a connection to the database
# inputs: database file
# outputs: the connection to the db or none.
#creating connection with SQ database
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None

def user_id():
   query = "SELECT 'fname' FROM users"
   con = create_connection(DB_NAME)
   cur = con.cursor()
   cur.execute(query)
   con.close()

@app.route('/')
def render_homepage():
    con = create_connection(DB_NAME)
    query = "SELECT category, id FROM categories" #selects relevant info from the right table
    cur = con.cursor()
    cur.execute(query)
    categories_list = cur.fetchall()
    con.close()
    return render_template("home.html", logged_in=is_logged_in(), categories=categories_list) #displays the html

@app.route('/teacher')
def render_teacher():
    con = create_connection(DB_NAME)
    query = "SELECT category, id FROM categories"
    cur = con.cursor()
    cur.execute(query)
    categories_list = cur.fetchall()
    con.close()
    return render_template("teacher.html", logged_in=is_logged_in(), category=categories_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect('/')
    if request.method == "POST":
        # .strip() ignores any leading or trailing spaces in the user input
        email = request.form['email'].strip() #requests the right data from the form the user filled out - in this case the email
        password = request.form['password'].strip()

        query = """SELECT id, fname, password FROM users WHERE email = ?"""
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
            return redirect('/login?error=email+invalid+or+password+incorrect') #if password not matching with corresponding email

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        print(session)
        return redirect('/')
    return render_template('login.html')


@app.route('/signup', methods =['GET','POST'])
def render_signup_page():
    if is_logged_in():
        return redirect('/') #if logged in, redirect to home page
    if request.method == 'POST':
        print(request.form)
        # .strip() ignores any leading or trailing spaces in the user input
        fname = request.form.get('fname').strip().title() #title auto capitalises
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower() #lower makes everything lower case
        password = request.form.get('pass')
        password2 = request.form.get('pass2')

        if password != password2:
            return redirect('/signup?error=Passwords+dont+match') #if passwords don't match, then error

        hashed_password = bcrypt.generate_password_hash(password) #generates an encrypted password for security

        con = create_connection(DB_NAME)

        query = "INSERT INTO users(id,fname,lname,email,password) VALUES(NULL,?,?,?,?)" #Inserts the user inputs into the users table

        cur = con.cursor()
        try:
            cur.execute(query,(fname,lname,email,hashed_password))
        except sqlite3.IntegrityError:
            return redirect('signup?error=Email+is+already+used') #doesn't let same email sign up twice
        con.commit()
        con.close()
        return redirect('/login') #redirects to login page once signed up


    return render_template('signup.html', logged_in=is_logged_in())

#@app.route('/words')
#def render_words(categoryid):
 #   con = create_connection(DB_NAME)
  #  query = "SELECT english, maori, level, added_by, definition, image, id FROM words"
   # cur = con.cursor()
    #cur.execute(query)
   # words_list = cur.fetchall()
   # con.close()

#     if words_list is empty - render addnewword
   # return render_template("edit.html", words = words_list, logged_in = is_logged_in())

@app.route('/edit', methods = ['GET', 'POST'])
def render_edit():

    if request.method == "GET":
        return render_template("edit.html", logged_in=is_logged_in())

    if request.method == "POST":
        print(request.form)

     # .strip() ignores any leading or trailing spaces in the user input
        english = request.form.get('english')
        maori = request.form.get('maori') #title auto capitalises
        definition = request.form.get('definition')
        level = request.form.get('level')
        added_by = request.form.get('added_by')
        image = 'noimage'
        con = create_connection(DB_NAME)
      #  userid = session['userid']

        query = """INSERT INTO words(id, english, maori, definition, level, added_by, image) VALUES(NULL,?,?,?,?,?,?)"""
        cur = con.cursor()
        cur.execute(query, (english, maori, definition, level, added_by, image, ))

        con.commit()
        con.close()
    return render_template("edit.html", logged_in = is_logged_in())




@app.route('/dictionary')
def render_dictionary():
    con = create_connection(DB_NAME)
    query = "SELECT english, maori, level, userid, image, id FROM words"
    cur = con.cursor()
    cur.execute(query)
    words_list = cur.fetchall()
    con.close()
    if request.method =='POST':
        print(request.form)
        delete_word = request.form['delete_word'].strip().lower()
        print(delete_word)
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute("DELETE FROM words WHERE english=?", (delete_word, ))
        con.commit()
        con.close()
    return render_template("dictionary.html", words= words_list, logged_in =is_logged_in())

@app.route('/words/<xword>')
def render_word_page(xword):
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute ("SELECT english, maori, level, definition, userid, image, id FROM words WHERE english=?", (xword, ))
    user_data = cur.fetchall()
    con.commit()
    con.close()
    print(user_data)
    return render_template('words.html', logged_in = is_logged_in(), words=user_data)



#@app.route('/categories')
#def render_categories():
 #   con = create_connection(DB_NAME)
  #  query = "SELECT category, id FROM categories"
   # cur = con.cursor()
    #cur.execute(query)
 #   categories_list = cur.fetchall()
  #  con.close()
   # return render_template("categories.html", categories = categories_list, logged_in = is_logged_in())


#adding option to add new categories
#@app.route('/edit', methods =['GET','POST'])
#def render_edit():

 #  if request.method == 'POST':


     # .strip() ignores any leading or trailing spaces in the user input
    #    word = request.form.get('english').strip().title() #title auto capitalises

   #     con = create_connection(DB_NAME)

    #    query = "INSERT INTO categories(id,category) VALUES(NULL,?)"

     #   cur = con.cursor()
      #  try:
       #     cur.execute(query, (category,)) #the extra comma at the end makes it a tuple( takes words as opposed to characters)
        #except sqlite3.IntegrityError:
         #   return redirect('signup?error=category+is+already+used') #doesn't let same category be added twice
        #con.commit()
        #con.close()
   # return render_template("edit.html", logged_in = is_logged_in())


def is_logged_in():
    if session.get('email') is None:
        print('Not logged in')
        return False
    else:
        print('Logged in')
        return True


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')

def create_connection(db_file):
   """create a connection to the sqlite db"""
   try:
       connection = sqlite3.connect(db_file)
       connection.execute('pragma foreign_keys=ON')
       return connection
   except Error as e:
       print(e)

   return None


app.run(host="0.0.0.0", debug=True)