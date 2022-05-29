from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime


DB_NAME = "maori_dictionary.db" #database name

#initial settings

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "secret_key"



#creating connection with SQ database
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:  #if connection to database fails
        print(e)

    return None

#maps URL to specific function, in this case home page
@app.route('/')
def render_homepage(): #creates function
    return render_template("home.html", logged_in=is_logged_in())  # displays the html, shows logged in status


#mapping URL to function for teacher verification page
@app.route('/teacher')
def render_teacher():
    return render_template("teacher.html", logged_in=is_logged_in())


@app.route('/login', methods=['GET', 'POST']) #GET is when viewing something without changing, whereas POST is when changing something
def login():
    if is_logged_in():
        return redirect('/') #redirects to home page
    if request.method == "POST":
        # .strip() ignores any leading or trailing spaces in the user input
        email = request.form['email'].strip() #requests the right data from the form the user filled out - in this case the email
        password = request.form['password'].strip()

        query = """SELECT id, fname, password FROM users WHERE email = ?""" #query gathers data from the table, email is a parameter given by the user
        con = create_connection(DB_NAME) #function call to create connection with database
        cur = con.cursor() #retrieves data after the select statement
        cur.execute(query, (email,)) #executes the query, and email is passed
        user_data = cur.fetchall()  #gets all the information for the specific user
        con.close() #closes connection
        try:
            userid = user_data[0][0] #gets userid
            firstname = user_data[0][1] #gets first name
            db_password = user_data[0][2] #gets password
        except IndexError:
            return redirect('/login?error=email+invalid+or+password+incorrect') #if firstname, userid or db_password not found

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=email+invalid+or+password+incorrect") #if password does not match password in database

        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+8+characters+or+more') #if password is less than 8 characters

#saves email, userid and firstname for the session
        session['email'] = email #
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
        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+8+characters+or+more') #doesn't allow password of less than 8 characters
        hashed_password = bcrypt.generate_password_hash(password) #generates an encrypted password for security

        con = create_connection(DB_NAME)

        query = "INSERT INTO users(id,fname,lname,email,password) VALUES(NULL,?,?,?,?)" #Inserts the user inputs into the users table

        cur = con.cursor()
        try:
            cur.execute(query,(fname,lname,email,hashed_password)) #executes db query
        except sqlite3.IntegrityError:
            return redirect('signup?error=Email+is+already+used') #doesn't let same email sign up twice
        con.commit()
        con.close()
        return redirect('/login') #redirects to login page once signed up


    return render_template('signup.html', logged_in=is_logged_in())

#code for adding a new word
@app.route('/add_word', methods = ['GET', 'POST'])
def render_add_word():

    if request.method == "GET":
        return render_template("edit.html", logged_in=is_logged_in())

    if request.method == "POST":
        print(request.form)

    #retrieving the user inputs
     # .strip() ignores any leading or trailing spaces in the user input
        english = request.form.get('english').strip().lower()
        if len(english) > 30: #doesn't allow the word to be longer than 30 characters
            return redirect('/dictionary?error=word+must+be+less+than+30+characters')
        maori = request.form.get('maori').strip().lower() #title auto capitalises
        if len(maori) > 30: #doesn't allow the word to be longer than 30 characters
            return redirect('/dictionary?error=word+must+be+less+than+30+characters')
        definition = request.form.get('definition').strip().lower()
        if len(definition) > 200: #doesn't allow the definition to be longer than 200 characters
            return redirect('/dictionary?error=definition+must+be+less+than+30+characters')
        level = request.form.get('level')
        if len(level) > 99: #doesn't allow the year level to be greater than 2 digits
            return redirect('/dictionary?error=year+must+be+less+than+3+digits')

        added_by = session['firstname'].strip().lower() #shows who the word was added by
        image = 'noimage.png' #automatically uses noimage.png for every added image
        timestamp = datetime.now() #gets the current date and time of when the word was added
        con = create_connection(DB_NAME)
        userid = session['userid'] #extracts the session userid

        #inserts the user inputs into the words table
        query = """INSERT INTO words(id, english, maori, userid, definition, level, added_by, image, timestamp) VALUES(NULL,?,?,?,?,?,?,?,?)"""
        cur = con.cursor()
        try:
            cur.execute(query, (english, maori, userid, definition, level, added_by, image, timestamp)) # the commas make the fields a tuple(takes words as opposed to characters)
        except sqlite3.IntegrityError:
           return redirect('/dictionary?error=word+is+already+used') #doesn't let same word be added twice

        con.commit()
        con.close()
    return render_template("edit.html", logged_in = is_logged_in())




@app.route('/dictionary', methods = ['GET', 'POST'])
def render_dictionary():
    con = create_connection(DB_NAME)
    query = "SELECT english FROM words ORDER BY id" #initially displays all the words in english, and sorts them by id so that newly added words are shown at the bottom
    cur = con.cursor()
    cur.execute(query)
    words_list = cur.fetchall()
    con.close()

    return render_template("dictionary.html", words= words_list, logged_in = is_logged_in())

@app.route('/DeleteConfirm', methods = ['GET', 'POST']) #code for delete confirmation
def delete_confirm():
        delete_word = request.form.get("Delete_Word").lower() #gets the word to be deleted
        return render_template("delete_confirm.html", words=delete_word)



@app.route('/DeleteWord/<words>', methods = ['GET', 'POST']) #code for deleting the word

def delete_word(words):

    print(request.form)
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute("DELETE FROM words WHERE english=?", (words, )) #deletes the english word and associated fields from the dictionary
    con.commit()
    con.close()
    return redirect('/dictionary')

@app.route('/words/<xword>') #detailed display of words once clicking on the intial display
def render_word_page(xword): #xword is the word that is being clicked on

    if is_logged_in(): #only needs userid if logged in which allows people who aren't logged in to also view the dictionary
        userid = session['userid']
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute ("SELECT english, maori, level, definition, added_by, image, timestamp, id FROM words WHERE english=?", (xword, )) #executes query
    user_data = cur.fetchall()
    con.commit()
    con.close()
    print(user_data)
    return render_template('words.html', logged_in = is_logged_in(), words=user_data)

#function to check if user is logged in
def is_logged_in():
    if session.get('email') is None: #if email not entered, then user isn't logged in
        print('Not logged in')
        return False
    else:
        print('Logged in') #if email is entered then user is logged in
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


app.run(host="0.0.0.0", debug=True) #debugger