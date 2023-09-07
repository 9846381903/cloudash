# importing binaries
import os
import requests
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
import mysql.connector as c

# main function getting regions details
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

        # function for region code
        def region_code():
            try:
                credential = DefaultAzureCredential()
                subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
                subscription_client = SubscriptionClient(credential)
                response = subscription_client.subscriptions.list_locations(subscription_id)
                region_codes_list = []
                for region in response:
                    region_code = region.name
                    region_codes_list.append(region_code)
                return region_codes_list
            except Exception as e:
                print(f"Error in az_region.py region_code: {e}")
                return "500 Internal Server Error"

        # function for region name
        def get_region_details(region_code):
            try:
                credential = DefaultAzureCredential()
                subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
                client = SubscriptionClient(credential)
                regions = client.subscriptions.list_locations(subscription_id)
                for r in regions:
                    if r.name == region_code:
                        region_name = r.display_name
                        region_name = region_name.replace('Europe', 'EU')
                        return region_name
                return ""
            except Exception as e:
                print(f"Error in az_region.py get_region_details: {e}")
                return "500 Internal Server Error"

        # tail end of the code, retrieves the region code, region name, latitude and longitude
        region_codes_list = region_code()
        for code in region_codes_list:
            region_name = get_region_details(code)
            response = requests.get(f"https://nominatim.openstreetmap.org/search?q={region_name}&format=json")
            data = response.json()
            if not data:
                cursor.execute("DELETE FROM cloud_region WHERE CLOUD = %s AND CLD_REGION = %s AND LOCATION = %s", ('azure', code, region_name))
                connect.commit()
            else:
                latitude = data[0]['lat']
                longitude = data[0]['lon']
                cursor.execute("SELECT * FROM cloud_region WHERE CLOUD = %s AND CLD_REGION = %s AND LOCATION = %s", ('azure', code, region_name))
                result = cursor.fetchone()
                if result:
                    cursor.execute("UPDATE cloud_region SET LATITUDE = %s, LONGITUDE = %s WHERE CLOUD = %s AND CLD_REGION = %s AND LOCATION = %s", (latitude, longitude, 'azure', code, region_name))
                else:
                    cursor.execute("INSERT INTO cloud_region(CLOUD, CLD_REGION, LOCATION, LATITUDE, LONGITUDE)VALUES(%s,%s,%s,%s,%s)", ('azure', code, region_name, latitude, longitude))
                connect.commit()
        return 'Data retrieval and insertion into database successful'
    except Exception as e:
        print(f"Error in az_region.py main_region_function: {e}")
        return "500 Internal Server Error"

# calling main function
main_region_function()
