# importing binaries
import os
import boto3
import json
from pkg_resources import resource_filename
import mysql.connector as c

# main functon for getting price
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

        # function for getting instance type
        def get_instance_type_details():
            try:
                client = boto3.client('pricing', region_name='ap-south-1')
                paginator = client.get_paginator('get_attribute_values')
                iterator = paginator.paginate(ServiceCode='AmazonEC2', AttributeName='instanceType', PaginationConfig={'PageSize': 100})
                instance_types_list = []
                for instances in iterator:
                    instances_value = instances['AttributeValues']
                    for ec2 in instances_value:
                        for value in ec2.values():
                            if '.' in value:
                                instance_types_list.append(value)
                ec2 = boto3.client('ec2', region_name='ap-south-1')
                instance_types_lists = []
                for instance_type in instance_types_list:
                    try:
                        response = ec2.describe_instance_types(InstanceTypes=[instance_type])
                        instance_info = response['InstanceTypes'][0]
                        ram = instance_info['MemoryInfo']['SizeInMiB'] / 1024
                        cpu = instance_info['VCpuInfo']['DefaultVCpus']
                        instance_types_lists.append({'Instance Type': instance_type, 'vCPU': cpu, 'RAM (GB)': ram})
                    except:
                        continue
                return instance_types_lists
            except Exception as e:
                print(f"Error in aws_price.py get_instance_type_details function: {e}")
                return "500 Internal Server Error"

        # function for getting regions
        def get_region_name(region_code):
            try:
                endpoint_file = resource_filename('botocore', 'data/endpoints.json')
                with open(endpoint_file, 'r') as f:
                    endpoint_data = json.load(f)
                region_name = endpoint_data['partitions'][0]['regions'][region_code]['description']
                region_name = region_name.replace('Europe', 'EU')
                return region_name
            except Exception as e:
                print(f"Error in aws_price.py get_region_name function: {e}")
                return "500 Internal Server Error"

        # function for getting instance price
        def get_ec2_instance_hourly_price(region_code, instance_type, operating_system, preinstalled_software='NA', tenancy='Shared', is_byol=False):
            try:
                region_name = get_region_name(region_code)
                if is_byol:
                    license_model = 'Bring your own license'
                else:
                    license_model = 'No License required'
                if tenancy == 'Host':
                    capacity_status = 'AllocatedHost'
                else:
                    capacity_status = 'Used'
                filters = [
                    {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': capacity_status},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': tenancy},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': operating_system},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': preinstalled_software},
                    {'Type': 'TERM_MATCH', 'Field': 'licenseModel', 'Value': license_model},
                ]
                pricing_client = boto3.client('pricing', region_name='ap-south-1')
                response = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=filters)
                for price in response['PriceList']:
                    price = json.loads(price)
                    for on_demand in price['terms']['OnDemand'].values():
                        for price_dimensions in on_demand['priceDimensions'].values():
                            price_value = price_dimensions['pricePerUnit']['USD']
                    return float(price_value)
                return None
            except Exception as e:
                print(f"Error in aws_price.py get_ec2_instance_hourly_price function: {e}")
                return "500 Internal Server Error"

        # tail end of the code, retrieves the instance prices from all regions for the first instance type and proceeds to the next type
        ec2_client = boto3.client('ec2', region_name='ap-south-1')
        response = ec2_client.describe_regions(AllRegions=True)
        regions = response['Regions']
        region_code_list = []
        for region in regions:
            region_code = region['RegionName']
            region_code_list.append(region_code)
        region_code_list = sorted(region_code_list)
        ec2_instance_types_list = get_instance_type_details()
        for ec2_type in ec2_instance_types_list:
            instance_type = ec2_type["Instance Type"]
            vcpu = ec2_type["vCPU"]
            memory = ec2_type["RAM (GB)"]
            # get the existing data from the database
            select_data = "SELECT * FROM vm_price WHERE CLD_SKU=%s AND CLOUD='aws'"
            values = (instance_type,)
            cursor.execute(select_data, values)
            existing_data = cursor.fetchall()
            for region in regions:
                region_code = region['RegionName']
                operating_system = 'Linux'
                ec2_instance_price = get_ec2_instance_hourly_price(
                    region_code=region_code,
                    instance_type=instance_type,
                    operating_system=operating_system,
                )
                region_name = get_region_name(region_code)
                if ec2_instance_price is not None:
                    vmsku = 'aws' + region_code + instance_type
                    # check if the data already exists in the database
                    result = [data for data in existing_data if data[5] == region_code and data[2] == instance_type]
                    if len(result) == 0:
                        # insert new data if it doesn't already exist
                        insert_data = "INSERT INTO vm_price(VMSKU, CLOUD, CLD_SKU, CPU, RAM, CLD_REGION, PRICE)VALUES(%s,%s,%s,%s,%s,%s,%s)"
                        values = (vmsku, 'aws', instance_type, vcpu, memory, region_code, ec2_instance_price)
                        cursor.execute(insert_data, values)
                    else:
                        if result[0][6] != ec2_instance_price:
                            # update the price if it has changed
                            update_data = "UPDATE vm_price SET PRICE=%s WHERE VMSKU=%s AND CLD_SKU=%s AND CLD_REGION=%s AND CLOUD='aws'"
                            values = (ec2_instance_price, vmsku, instance_type, region_code)
                            cursor.execute(update_data, values)
                else:
                    # check if the data already exists in the database for the cloud 'aws'
                    result = [data for data in existing_data if data[5] == region_code and data[2] == instance_type]
                    if len(result) > 0:
                        # delete the data if it is no longer available
                        delete_data = "DELETE FROM vm_price WHERE CLD_SKU=%s AND CLD_REGION=%s AND CLOUD='aws'"
                        values = (instance_type, region_code)
                        cursor.execute(delete_data, values)
            connect.commit()
        return 'Data retrieval and insertion into database successful'
    except Exception as e:
        print(f"Error in aws_price.py main_price_function function: {e}")
        return"500 Internal Server Error"

# calling main function
main_price_function()
