from flask import render_template, session
class User():

    def do_the_login(self,username):
        session['login'] = True
        session['username'] = username
        return "I would be logging in now %s" % username

    def show_the_login_form(self):
        return render_template("user/user.html")