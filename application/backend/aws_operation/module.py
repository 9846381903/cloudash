# importing binaries
from flask import Flask, request
from aws import launchvm, rebootvm, stopvm, startvm, terminatevm
from flask_cors import CORS  

# intialising  flask application
app = Flask(__name__)
CORS(app)  

# endpoint for launching instance
@app.route('/api/aws/launchvm', methods=['POST'])
def call_launchvm():
    username = request.json.get('username')
    public_key = request.json.get('public_key')
    vmid = request.json.get('vmid')
    cloud = request.json.get('cloud')
    region = request.json.get('region')
    instance_type = request.json.get('instance_type')
    return launchvm(username, public_key, vmid, cloud, region, instance_type)

# endpoint for rebboting instance
@app.route('/api/aws/rebootvm', methods=['POST'])
def call_rebootvm():
    instance_id = request.json.get('instance_id')
    region = request.json.get('region')
    return rebootvm(instance_id, region)

# endpoint for stopping instance
@app.route('/api/aws/stopvm', methods=['POST'])
def call_stopvm():
    instance_id = request.json.get('instance_id')
    region = request.json.get('region')
    return stopvm(instance_id, region)

# endpoint for starting instance
@app.route('/api/aws/startvm', methods=['POST'])
def call_startvm():
    instance_id = request.json.get('instance_id')
    region = request.json.get('region')
    return startvm(instance_id, region)

# endpoint for terminating instance
@app.route('/api/aws/terminatevm', methods=['POST'])
def call_terminatevm():
    instance_id = request.json.get('instance_id')
    region = request.json.get('region')
    return terminatevm(instance_id, region)

# main function for enabling port
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5002)
