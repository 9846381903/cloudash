# importing binaries
import mysql.connector as c
import bcrypt
import os

# function to authenticate username and password
def user_authentication(username_or_email, password):
    if not username_or_email or not password:
        return {'error': 'Username/email and password are required'}, 400
    # authenticate the user
    authentication_result = authenticate(username_or_email, password)
    if 'authenticated' in authentication_result and authentication_result['authenticated']:
        token, username, email = authentication_result['token'], authentication_result['username'], authentication_result['email']
        return {'authenticated': True, 'token': token, 'username': username, 'email': email}, 200
    else:
        return {'authenticated': False, 'error': 'Incorrect username or password'}, 401

# function to authenticate a user
def authenticate(username_or_email, entered_password):
    # setting up the database
    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    # connect to the database
    connect = c.connect(host=host, user=user, password=db_password, database='clouddash')
    cursor = connect.cursor()
    # query the database for the user
    cursor.execute("SELECT PASSWORD, TOKEN, USERNAME, EMAIL FROM users WHERE USERNAME=%s OR EMAIL=%s", (username_or_email, username_or_email))
    result = cursor.fetchone()
    # if the user exists, check the password
    if result:
        stored_password, token, username, email = result
        if bcrypt.checkpw(entered_password.encode(), stored_password.encode()):
            return {'authenticated': True, 'token': token, 'username': username, 'email': email}
    return {'authenticated': False}
