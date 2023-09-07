# importing binaries
from flask import Flask, request, jsonify
from flask_cors import CORS  
from signup import register, verify_otp
from login import user_authentication

# initialising  flask application
app = Flask(__name__)
CORS(app)  

# endpoint for registering username
@app.route('/register', methods=['POST'])
def call_register():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    confirm_password = request.json.get('confirm_password')
    return register(username, email, password, confirm_password)

# endpoint for verifying otp
@app.route('/verify-otp', methods=['POST'])
def call_verify_otp():
    email = request.json.get('email')
    otp = request.json.get('otp')
    if verify_otp(email, otp):
        return {'message': 'OTP verification successful'}
    else:
        return {'error': 'Incorrect OTP'}

# endpoint for authenticating username
@app.route('/authenticate', methods=['POST'])
def call_user_authentication():
    username_or_email = request.json.get('username_or_email')
    password = request.json.get('password')
    return user_authentication(username_or_email, password)

# main function for enabling port
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
