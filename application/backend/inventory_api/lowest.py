#importing binaries
import os
import mysql.connector as c
from flask import Flask, jsonify, request

#function for getting data from the database according to the cpu and ram input
def main_data_function(cpu, ram):
    try:
        #database credential
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        #accessing database
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        #queries for fetching the lowest price instance_type
        query = None
        if cpu is not None and ram is None:
            query = f"SELECT * FROM cloud_region JOIN vm_price ON cloud_region.CLOUD = vm_price.CLOUD AND cloud_region.CLD_REGION = vm_price.CLD_REGION WHERE vm_price.CPU >= {cpu} ORDER BY vm_price.PRICE ASC LIMIT 5"
        elif cpu is None and ram is not None:
            query = f"SELECT * FROM cloud_region JOIN vm_price ON cloud_region.CLOUD = vm_price.CLOUD AND cloud_region.CLD_REGION = vm_price.CLD_REGION WHERE vm_price.RAM >= {ram} ORDER BY vm_price.PRICE ASC LIMIT 5"
        else:
            query = f"SELECT * FROM cloud_region JOIN vm_price ON cloud_region.CLOUD = vm_price.CLOUD AND cloud_region.CLD_REGION = vm_price.CLD_REGION WHERE vm_price.CPU <= {cpu} AND vm_price.RAM <= {ram} ORDER BY vm_price.CPU DESC, vm_price.RAM DESC, vm_price.PRICE ASC LIMIT 5"
        cursor.execute(query)
        results = cursor.fetchall()
        data = []
        for result in results:
            data.append({'CLOUD': result[0], 'VMID': result[5], 'CLD_SKU': result[7], 'LOCATION': result[2], 'CLD_REGION': result[1], 'LATITUDE': result[3], 'LONGITUDE': result[4], 'PRICE': result[11]})
        cursor.close()
        connect.close()
        return jsonify(data)
    except Exception as e:
        print(f"Error in lowest.py main_data_function: {e}")
        return "500 Internal Server Error"
