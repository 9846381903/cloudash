#importing binaries
from flask import Flask, jsonify, request
from lowest import main_data_function
from flask_cors import CORS 

#intialising flask application
app = Flask(__name__)
CORS(app) 

#endpoint for fetching lowest price instance
@app.route('/clouddash/low_price/getvm', methods=['POST'])
def call_main_data_function():
    cpu = request.form.get('cpu',type=float)
    ram = request.form.get('ram',type=float)
    return main_data_function(cpu, ram)

#main function for port enabling
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)
