# importing binaries
import os
import mysql.connector as c
import requests
import subprocess
from flask import Flask, request, make_response, jsonify
import json

# passing api endpoints
api_endpoint = os.environ.get('API_ENDPOINT')
aws_api_endpoint = os.environ.get('AWS_API_ENDPOINT')
azure_api_endpoint = os.environ.get('AZURE_API_ENDPOINT')
register_url = os.environ.get('REGISTER_API_ENDPOINT') + '/register'
authenticate_url = os.environ.get('AUTHENTICATE_API_ENDPOINT') + '/authenticate'
verify_url = os.environ.get('VERIFY_API_ENDPOINT') + '/verify-otp'

# authorizing bearer token
def is_authorized():
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        token = auth_header.split('Bearer ')[-1]
        query = "SELECT COUNT(*) FROM users WHERE TOKEN = %s"
        cursor.execute(query, (token,))
        result = cursor.fetchone()
        if result[0] == 1:
            query = "SELECT USERNAME FROM users WHERE TOKEN = %s"
            cursor.execute(query, (token,))
            result = cursor.fetchone()
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Error in controller.py is_authorized function: {e}")
        return "500 Internal Server Error"

# function for invoking launch api
def launchvm(cpu, ram, public_key):
    try:
        username = is_authorized()
        if username is None:
            return 'Unauthorized', 401
        curl_output = subprocess.check_output(["curl", "-X", "POST", "{}/clouddash/low_price/getvm".format(api_endpoint), "-d", f"ram={ram}", "-d", f"cpu={cpu}"])
        instance_info = json.loads(curl_output)
        vmid = instance_info[0]['VMID']
        cloud = instance_info[0]['CLOUD']
        region = instance_info[0]['CLD_REGION']
        instance_type = instance_info[0]['CLD_SKU']
        # choose endpoint based on cloud type
        if cloud.lower() == 'aws':
            endpoint = aws_api_endpoint
        elif cloud.lower() == 'azure':
            endpoint = azure_api_endpoint
        else:
            return 'Unknown cloud type', 400
        response = requests.post('{}/api/{}/launchvm'.format(endpoint, cloud.lower()), json={'username': username, 'public_key': public_key, 'vmid': vmid, 'cloud': cloud, 'region': region, 'instance_type': instance_type}, headers=request.headers)
        return response.text
    except Exception as e:
        print(f"Error in controller.py launchvm function: {e}")
        return "500 Internal Server Error"

# function for invoking reboot api
def rebootvm(unique_id):
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        username = is_authorized()
        if username is None:
            return 'Unauthorized', 401
        unique_id = request.json.get('unique_id')
        connect.autocommit = True
        cursor = connect.cursor()
        query = "SELECT COUNT(*) FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
        cursor.execute(query, (username, unique_id,))
        result = cursor.fetchone()
        if result[0] == 1:
            query = "SELECT ID, CLD_REGION, CLOUD FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
            cursor.execute(query, (username, unique_id,))
            instance_id, region, cloud = cursor.fetchone()
            # choose endpoint based on cloud type
            if cloud.lower() == 'aws':
                endpoint = aws_api_endpoint
            elif cloud.lower() == 'azure':
                endpoint = azure_api_endpoint
            else:
                return 'Unknown cloud type', 400
            response = requests.post('{}/api/{}/rebootvm'.format(endpoint, cloud.lower()), json={'instance_id': instance_id, 'region': region}, headers=request.headers)
            return response.text
        else:
            return 'Unauthorized', 401
    except Exception as e:
        print(f"Error in controller.py rebootvm function: {e}")
        return "500 Internal Server Error"
    
# function for invoking stop api
def stopvm(unique_id):
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        username = is_authorized()
        if username is None:
            return 'Unauthorized', 401
        unique_id = request.json.get('unique_id')
        connect.autocommit = True
        cursor = connect.cursor()
        query = "SELECT COUNT(*) FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
        cursor.execute(query, (username, unique_id,))
        result = cursor.fetchone()
        if result[0] == 1:
            query = "SELECT ID, CLD_REGION, CLOUD FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
            cursor.execute(query, (username, unique_id,))
            instance_id, region, cloud = cursor.fetchone()

            # choose endpoint based on cloud type
            if cloud.lower() == 'aws':
                endpoint = aws_api_endpoint
            elif cloud.lower() == 'azure':
                endpoint = azure_api_endpoint
            else:
                return 'Unknown cloud type', 400
            response = requests.post('{}/api/{}/stopvm'.format(endpoint, cloud.lower()), json={'instance_id': instance_id, 'region': region}, headers=request.headers)
            return response.text
        else:
            return 'Unauthorized', 401
    except Exception as e:
        print(f"Error in controller.py stopvm function: {e}")
        return "500 Internal Server Error"

# function for invoking start api
def startvm(unique_id):
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        username = is_authorized()
        if username is None:
            return 'Unauthorized', 401
        connect.autocommit = True
        cursor = connect.cursor()
        query = "SELECT COUNT(*) FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
        cursor.execute(query, (username, unique_id,))
        result = cursor.fetchone()
        if result[0] == 1:
            query = "SELECT ID, CLD_REGION, CLOUD FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
            cursor.execute(query, (username, unique_id,))
            instance_id, region, cloud = cursor.fetchone()
            # choose endpoint based on cloud type
            if cloud.lower() == 'aws':
                endpoint = aws_api_endpoint
            elif cloud.lower() == 'azure':
                endpoint = azure_api_endpoint
            else:
                return 'Unknown cloud type', 400
            response = requests.post('{}/api/{}/startvm'.format(endpoint, cloud.lower()), json={'instance_id': instance_id, 'region': region}, headers=request.headers)
            return response.text
        else:
            return 'Unauthorized', 401
    except Exception as e:
        print(f"Error in controller.py startvm function: {e}")
        return "500 Internal Server Error"

# function for invoking terminate api
def terminatevm(unique_id):
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        username = is_authorized()
        if username is None:
            return 'Unauthorized', 401
        unique_id = request.json.get('unique_id')
        connect.autocommit = True
        cursor = connect.cursor()
        query = "SELECT COUNT(*) FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
        cursor.execute(query, (username, unique_id,))
        result = cursor.fetchone()
        if result[0] == 1:
            query = "SELECT ID, CLD_REGION, CLOUD FROM provisioned_vm WHERE USERNAME = %s AND UNIQUE_ID = %s"
            cursor.execute(query, (username, unique_id,))
            instance_id, region, cloud = cursor.fetchone()
            # choose endpoint based on cloud type
            if cloud.lower() == 'aws':
                endpoint = aws_api_endpoint
            elif cloud.lower() == 'azure':
                endpoint = azure_api_endpoint
            else:
                return 'Unknown cloud type', 400
            response = requests.post('{}/api/{}/terminatevm'.format(endpoint, cloud.lower()), json={'instance_id': instance_id, 'region': region}, headers=request.headers)
            return response.text
        else:
            return 'Unauthorized', 401
    except Exception as e:
        print(f"Error in controller.py terminatevm function: {e}")
        return "500, Internal Server Error"

# function for listing launched instance
def listinstances():
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        username = is_authorized()
        if username is None:
            return 'Unauthorized', 401
        query = "SELECT UNIQUE_ID, IP FROM provisioned_vm WHERE USERNAME = %s"
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        cursor.execute(query, (username,))
        results = cursor.fetchall()
        cursor.close()
        connect.close()
        formatted_results = [{'UNIQUE_ID': r[0], 'IP': r[1]} for r in results]
        return jsonify(formatted_results)
    except Exception as e:
        print(f"Error in controller.py listinstances function: {e}")
        return "500 Internal Server Error"

# function for user registration
def register_user():
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        register_data = request.get_json()
        register_response = requests.post(register_url, json=register_data)
        register_result = register_response.json()
        cursor.close()
        connect.close()
        return jsonify(register_result)
    except Exception as e:
        print(f"Error in controller.py register_user function: {e}")
        return "500 Internal Server Error"

# function for user authentication
def authenticate_user():
    try:
        # accessing database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        authenticate_data = request.get_json()
        authenticate_response = requests.post(authenticate_url, json=authenticate_data)
        authenticate_result = authenticate_response.json()
        cursor.close()
        connect.close()
        return jsonify(authenticate_result)
    except Exception as e:
        print(f"Error in controller.py authenticate_user function: {e}")
        return "500 Internal Server Error"

# function for otp verification
def verify_otp_from_user():
    try:
        # accessing the data from request
        verify_data = request.get_json()
        # making a POST request to the verify endpoint
        verify_response = requests.post(verify_url, json=verify_data)
        verify_result = verify_response.json()
        return jsonify(verify_result)
    except Exception as e:
        print(f"Error in controller.py verify_otp_from_user function: {e}")
        return "500 Internal Server Error"
