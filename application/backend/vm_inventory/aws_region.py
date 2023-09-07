# importing binaries
import os
import boto3
import json
from pkg_resources import resource_filename
import requests
import mysql.connector as c

# function for extracting region
def get_region_name(region_code):
    try:
        endpoint_file = resource_filename('botocore', 'data/endpoints.json')
        with open(endpoint_file, 'r') as f:
            endpoint_data = json.load(f)
        region_name = endpoint_data['partitions'][0]['regions'][region_code]['description']
        region_name = region_name.replace('Europe', 'EU')
        return region_name
    except Exception as e:
        print(f"Error in aws_region.py get_region_name function: {e}")
        return "500 Internal Server Error"

# function for extracting region_code, city, latitude, longitude and inserting data to the database
def main_region_function():
    try:
        # passing database environment variable
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        # creating database and table
        connect = c.connect(host=host, user=user, password=password)
        cursor = connect.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS clouddash")
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS cloud_region(CLOUD VARCHAR(100), CLD_REGION VARCHAR(100), LOCATION VARCHAR(100), LATITUDE VARCHAR(100), LONGITUDE VARCHAR(100))")
        # extracting region_code, city, latitude, longitude and inserting data to the database
        ec2_client = boto3.client('ec2', region_name='ap-south-1')
        response = ec2_client.describe_regions(AllRegions=True)
        regions = response['Regions']
        for region in regions:
            region_code = region['RegionName']
            region_name = get_region_name(region_code)
            if region_name == "":
                continue
            city = region_name.split("(")[-1].split(")")[0]
            url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error retrieving data from OpenStreetMap for region {region_code}: HTTP error {response.status_code}")
                continue
            data = response.json()
            if not data:
                cursor.execute("DELETE FROM cloud_region WHERE CLOUD = %s AND CLD_REGION = %s AND LOCATION = %s", ('aws', region_code, city))
                connect.commit()
            else:
                latitude = data[0]['lat']
                longitude = data[0]['lon']
                cursor.execute("SELECT * FROM cloud_region WHERE CLOUD = %s AND CLD_REGION = %s AND LOCATION = %s", ('aws', region_code, city))
                result = cursor.fetchone()
                if result:
                    cursor.execute("UPDATE cloud_region SET LATITUDE = %s, LONGITUDE = %s WHERE CLOUD = %s AND CLD_REGION = %s AND LOCATION = %s", (latitude, longitude, 'aws', region_code, city))
                else:
                    cursor.execute("INSERT INTO cloud_region(CLOUD, CLD_REGION, LOCATION, LATITUDE, LONGITUDE)VALUES(%s,%s,%s,%s,%s)", ('aws' ,region_code, city, latitude, longitude))
                connect.commit()
        return 'Data retrieval and insertion into database successful'
    except Exception as e:
        print(f"Error in aws_region.py main_region_function: {e}")
        return "500 Internal Server Error"
    
# calling main function
main_region_function()
