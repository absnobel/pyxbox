#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, redirect
#from flask_socketio import SocketIO, emit
# from flask.ext.sqlalchemy import SQLAlchemy
#from flask_login import LoginManager
import logging
from logging import Formatter, FileHandler
from forms import *
import os
import webbrowser
import asyncio
from aiohttp import ClientSession, ClientResponseError
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.exceptions import AuthenticationException
from xbox import *
client_id = ''
client_secret = ''
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
#db = SQLAlchemy(app)
#socketio = SocketIO(app)
#login_manager = LoginManager()
#login_manager.init_app(app)
auth_mgr = None

# Interesting bit here we need to store a unique id for each session... 
# so the plan here is
# 1. provide anonymous user to index with login button
# a. login will redirect to xbox ms login screen.. callback to auth/callback route with token
# b. Store token in mem or db with session id
# 2. protect the logged in route '/xbox'
# 3. create a websockets event that listens for 'getMe' 
# socketio getme event
# assuming i understand the logic current_user will be populated with the code
# 5. current_user will be autopopulated with session id and if overridden could add the xbox token
# 6. use the api and token to retrieve gamertag and gamerpic url emitting the message back to client 
# 7. Client will then display the received info. WIN!

# Automatically tear down SQLAlchemy.
'''
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
'''

# Login required decorator.
'''
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap
'''
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
#@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/auth/callback')
async def auth_callback():
    session = ClientSession()
    
    auth_mgr = AuthenticationManager(
        session, client_id, client_secret, "http://localhost:5000/auth/callback"
    )
    error = request.args.get("error")
    if error:
        description = request.args.get("error_description")
        print(f"Error in auth_callback: {description}")
        return
    # Run in task to not make unsuccessful parsing the HTTP response fail

    code = request.args.get("code")
    try:
        await auth_mgr.request_tokens(code)
    except ClientResponseError:
              print("Could not refresh tokens")
              

        # with open(tokens_file, mode="w") as f:
        #       f.write(auth_mgr.oauth.json())
    print(f'Refreshed tokens in {auth_mgr.oauth.json()}!')

    xbl_client = XboxLiveClient(auth_mgr)
    profile = await xbl_client.profile.get_profile_by_xuid(xbl_client.xuid)
    return render_template('pages/placeholder.loggedin.html', profile=profile)

@app.route('/')
def home():
    return render_template('pages/placeholder.home.html')


@app.route('/about')
def about():
    return render_template('pages/placeholder.about.html')


@app.route('/login')
async def login():
    
    session = ClientSession()
    
    auth_mgr = AuthenticationManager(
        session, client_id, client_secret, "http://localhost:5000/auth/callback"
    )

    auth_url = auth_mgr.generate_authorization_url()
    return redirect(auth_url)
           


@app.route('/register')
def register():
    form = RegisterForm(request.form)
    return render_template('forms/register.html', form=form)


@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)

# Error handlers.


@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
