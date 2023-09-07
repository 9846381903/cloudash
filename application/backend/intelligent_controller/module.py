# importing binaries
from flask import Flask, request, make_response, jsonify
from controller import is_authorized, launchvm, rebootvm, stopvm, startvm, terminatevm, listinstances, register_user, authenticate_user, verify_otp_from_user
import mysql.connector as c
from flask_cors import CORS

# intialising flask application
app = Flask(__name__)
CORS(app)

# endpoint for launching instance
@app.route('/v1/launchvm', methods=['POST'])
def call_launchvm():
    cpu = request.json.get('cpu')
    ram = request.json.get('ram')
    if not cpu and not ram:
        return 'Either CPU or RAM is required.', 400
    public_key = request.json.get('public_key')
    if not public_key:
        return 'Public key is required.', 400
    return launchvm(cpu, ram, public_key)

# endpoint for rebooting instance
@app.route('/v1/rebootvm', methods=['POST'])
def call_rebootvm():
    unique_id = request.json.get('unique_id')
    return rebootvm(unique_id)

# endpoint for stopping instance
@app.route('/v1/stopvm', methods=['POST'])
def call_stopvm():
    unique_id = request.json.get('unique_id')
    return stopvm(unique_id)

# endpoint for starting instance
@app.route('/v1/startvm', methods=['POST'])
def call_startvm():
    unique_id = request.json.get('unique_id')
    return startvm(unique_id)

# endpoint for terminating instance
@app.route('/v1/terminatevm', methods=['POST'])
def call_terminatevm():
    unique_id = request.json.get('unique_id')
    return terminatevm(unique_id)

# endpoint for listing instance
@app.route('/v1/listinstances', methods=['GET'])
def call_listinstances():
    return listinstances()

# endpoint for user registration
@app.route('/v1/register', methods=['POST'])
def call_register_user():
    return register_user()

# endpoint for user authentication
@app.route('/v1/authenticate', methods=['POST'])
def call_authenticate_user():
    return authenticate_user() 

# endpoint for OTP verification
@app.route('/v1/verify-otp', methods=['POST'])
def call_verify_otp_from_user():
    return verify_otp_from_user()

# main function for enabling port
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
