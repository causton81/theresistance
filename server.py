from flask import Flask, request, session
from user.user import User
app = Flask(__name__)
app.secret_key = 'asdsegwegdfgdfdfhT'
@app.route("/")
def slash():
    try:
        username = session['username']
    except KeyError:
        username = 'nobody'
    return "Game Time! %s" % username


@app.route("/login", methods=['GET','POST'])
def login():
    userClass = User()
    if request.method == 'POST':
        return userClass.do_the_login(request.form['username'])
    else:
        return userClass.show_the_login_form()

@app.route("/gm")
def gm():
    return "This is the gm page"



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
