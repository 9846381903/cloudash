# importing binaries
import os
import json
import requests
import mysql.connector as c
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.subscription import SubscriptionClient

# main function for getting price
def main_price_function():
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
        cursor.execute("CREATE TABLE IF NOT EXISTS vm_price(VMSKU VARCHAR(100), CLOUD VARCHAR(100), CLD_SKU VARCHAR(100), CPU VARCHAR(100), RAM VARCHAR(100), CLD_REGION VARCHAR(100), PRICE VARCHAR(100))")

        # function for vm type
        def vm_type_details():
            try:
                credential = DefaultAzureCredential()
                subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
                compute_client = ComputeManagementClient(credential, subscription_id)
                instance_types_lists = []
                for vm_size in compute_client.virtual_machine_sizes.list('eastus'):
                    cpu = vm_size.number_of_cores
                    ram = vm_size.memory_in_mb / 1024
                    instance_type = vm_size.name
                    instance_types_lists.append({'VM Type': instance_type, 'vCPU': cpu, 'RAM (GB)': ram})
                return instance_types_lists
            except Exception as e:
                print(f"Error in az_price.py vm_type_details function: {e}")
                return "500 Internal Server Error"

        # function for region
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
                print(f"Error in az_price.py region_code function: {e}")
                return "500 Internal Server Error"

        # function for finding price
        def vm_price(armRegionName, armSkuName, vCPU, RAM):
            try:
                table_data = []
                api_url = "https://prices.azure.com/api/retail/prices"
                query = f"serviceName eq 'Virtual Machines' and armRegionName eq '{armRegionName}' and armSkuName eq '{armSkuName}' and priceType eq 'Consumption'"
                response = requests.get(api_url, params={'$filter': query})
                json_data = json.loads(response.text)
                for item in json_data['Items']:
                    arm_sku_name = item['armSkuName']
                    arm_region_name = item['armRegionName']
                    unit_price = item['unitPrice']
                    if 'windows' not in item['productName'].lower() and 'low priority' not in item[
                        'meterName'].lower() and 'spot' not in item['meterName'].lower():
                        table_data.append([arm_sku_name, arm_region_name, vCPU, RAM, unit_price])
                nextPage = json_data['NextPageLink']
                while (nextPage):
                    response = requests.get(nextPage)
                    json_data = json.loads(response.text)
                    nextPage = json_data['NextPageLink']
                    for item in json_data['Items']:
                        arm_sku_name = item['armSkuName']
                        arm_region_name = item['armRegionName']
                        unit_price = item['unitPrice']
                        if 'windows' not in item['productName'].lower() and 'low priority' not in item[
                            'meterName'].lower() and 'spot' not in item['meterName'].lower():
                            table_data.append([arm_sku_name, arm_region_name, vCPU, RAM, unit_price])
                return table_data
            except Exception as e:
                print(f"Error in az_price.py vm_price function: {e}")
                return "500 Internal Server Error"

        # tail end of the code, retrieves the instance prices from all regions for the first instance type and proceeds to the next type
        region_codes_list = region_code()
        instance_details = vm_type_details()
        for instance in instance_details:
            vm_type = instance['VM Type']
            vcpu = instance['vCPU']
            ram = instance['RAM (GB)']
            for region in region_codes_list:
                price_data = vm_price(region, vm_type, vcpu, ram)
                if price_data:
                    arm_sku_name, arm_region_name, vCPU, RAM, unit_price = price_data[0]
                    vmsku = 'azure' + arm_region_name + arm_sku_name
                    # check if data already exists
                    check_data = "SELECT * FROM vm_price WHERE VMSKU=%s AND CLD_SKU=%s AND CLD_REGION=%s AND CLOUD='azure'"
                    values = (vmsku, arm_sku_name, arm_region_name)
                    cursor.execute(check_data, values)
                    result = cursor.fetchall()
                    if not result:
                        # insert new data if it doesn't already exist and unit_price is not 0.0
                        if unit_price != 0.0:
                            insert_data = "INSERT INTO vm_price(VMSKU, CLOUD, CLD_SKU, CPU, RAM, CLD_REGION, PRICE)VALUES(%s,%s,%s,%s,%s,%s,%s)"
                            values = (vmsku, 'azure', arm_sku_name, vCPU, RAM, arm_region_name, unit_price)
                            cursor.execute(insert_data, values)
                    else:
                        if result[0][6] != unit_price:
                            # update the price if it has changed and is not 0.0
                            if unit_price != 0.0:
                                update_data = "UPDATE vm_price SET PRICE=%s WHERE VMSKU=%s AND CLD_SKU=%s AND CLD_REGION=%s AND CLOUD='azure'"
                                values = (unit_price, vmsku, arm_sku_name, arm_region_name)
                                cursor.execute(update_data, values)
                else:
                    # check if the data already exists in the database for the cloud 'azure'
                    check_data = "SELECT * FROM vm_price WHERE VMSKU=%s AND CLD_SKU=%s AND CLD_REGION=%s AND CLOUD='azure'"
                    values = (vmsku, arm_sku_name, arm_region_name)
                    cursor.execute(check_data, values)
                    result = cursor.fetchall()
                    if result:
                        # delete the data if it is no longer available
                        delete_data = "DELETE FROM vm_price WHERE CLD_SKU=%s AND CLD_REGION=%s AND CLOUD='azure'"
                        values = (arm_sku_name, arm_region_name)
                        cursor.execute(delete_data, values)
            connect.commit()
        return 'Data retrieval and insertion into database successful'
    except Exception as e:
        print(f"Error in az_price.py main_price_function function: {e}")
        return "500 Internal Server Error"

# calling main funtion
main_price_function()
