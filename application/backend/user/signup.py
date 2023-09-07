# importing libraries
import hashlib
import secrets
import base64
import mysql.connector as c
import bcrypt
import os
from flask import Flask, jsonify, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# global variable to store otps and user data
otp_storage = {}

# function to register username with password
def register(username, email, password, confirm_password):
    if not username or not password or not email or not confirm_password:
        return jsonify({'error': 'Username, email, password, and confirm password are required'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Password and confirm password do not match'}), 400
    try:
        # check if username or email already exists
        if username_exists(username):
            return jsonify({'error': 'Username already taken'}), 409
        if email_exists(email):
            return jsonify({'error': 'Email already taken'}), 409
        # generate and send otp
        sender_email = 'akshay.s@clockhash.com'
        sender_password = os.environ.get('SMTP_TOKEN')
        subject = 'OTP Request'
        otp = generate_otp()
        send_email(sender_email, sender_password, email, subject, otp)
        # store the user data temporarily
        user_data = {
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': confirm_password
        }
        otp_storage[email] = {
            'user_data': user_data,
            'otp': otp
        }
        return jsonify({'message': 'OTP sent to your email'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 409

# function to check if username already exists
def username_exists(username):
    connect = get_database_connection()
    cursor = connect.cursor()
    cursor.execute("SELECT USERNAME FROM users WHERE USERNAME=%s", (username,))
    existing_user = cursor.fetchone()
    cursor.close()
    connect.close()
    return existing_user is not None

# function to check if email already exists
def email_exists(email):
    connect = get_database_connection()
    cursor = connect.cursor()
    cursor.execute("SELECT EMAIL FROM users WHERE EMAIL=%s", (email,))
    existing_email = cursor.fetchone()
    cursor.close()
    connect.close()
    return existing_email is not None

# function to generate token
def generate_token(username, email, password):
    # setting up the database
    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    # connect to the database
    connect = c.connect(host=host, user=user, password=db_password)
    cursor = connect.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS clouddash")
    connect = c.connect(host=host, user=user, password=db_password, database='clouddash')
    cursor = connect.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users(USERNAME VARCHAR(100), EMAIL VARCHAR(100), PASSWORD VARCHAR(100), TOKEN VARCHAR(100))")
    # check if username or email already exists
    cursor.execute("SELECT USERNAME, EMAIL FROM users WHERE USERNAME=%s OR EMAIL=%s", (username, email))
    existing_user = cursor.fetchone()
    if existing_user:
        # close the connection
        cursor.close()
        connect.close()
        raise ValueError("Username or email already taken")
    # generate a secure random token
    token = secrets.token_bytes(32)
    # base64 encode the data to create a token
    token = base64.b64encode(token).decode()
    # hash the password using bcrypt
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    # save the username, email, hashed password, and token to the database
    sql = "INSERT INTO users (USERNAME, EMAIL, PASSWORD, TOKEN) VALUES (%s, %s, %s, %s)"
    val = (username, email, password_hash.decode(), token)
    cursor.execute(sql, val)
    # commit the transaction
    connect.commit()
    # close the connection
    cursor.close()
    connect.close()
    return token

# function to get database connection
def get_database_connection():
    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    connect = c.connect(host=host, user=user, password=db_password, database='clouddash')
    return connect

def generate_otp():
    # generate a 6-digit otp
    return str(random.randint(100000, 999999))

def send_email(sender_email, sender_password, recipient_email, subject, otp):
    # smtp server settings
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    # create a MIME multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    # set the message content
    message = f'Your OTP is: {otp}'
    # attach the message to the MIME message
    msg.attach(MIMEText(message, 'plain'))
    # create a secure connection with the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    # login to the SMTP server
    server.login(sender_email, sender_password)
    # send the email
    server.send_message(msg)
    # clean up the connection
    server.quit()

def verify_otp(email, otp):
    # verify the entered otp against the otp stored in temporary storage
    stored_data = otp_storage.get(email)
    if stored_data and stored_data['otp'] == otp:
        del otp_storage[email]
        user_data = stored_data['user_data']
        generate_token(user_data['username'], user_data['email'], user_data['password'])  
        return True
    else:
        return False

