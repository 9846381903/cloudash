# importing binaries
import os
import boto3
import mysql.connector as c

# function for launching instance
def launchvm(username, public_key, vmid, cloud, region, instance_type):
    try:
        # database credential
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        # setting up the database
        connect = c.connect(host=host, user=user, password=password)
        cursor = connect.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS clouddash")
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS provisioned_vm(UNIQUE_ID VARCHAR(100), CLOUD VARCHAR(100), CLD_REGION VARCHAR(100), ID VARCHAR(100), TYPE VARCHAR(100), IP VARCHAR(100), USERNAME VARCHAR(100))")
        # create ssm and ec2 client objects
        ssm_client = boto3.client('ssm', region_name=region)
        ec2_client = boto3.client('ec2', region_name=region)
        # get the instance type information
        instance_types_info = ec2_client.describe_instance_types(InstanceTypes=[instance_type])['InstanceTypes']
        # getting the ami id of arm64 and armd
        image_ids = []
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        page_iterator = paginator.paginate(Path='/aws/service/canonical/ubuntu/server/20.04/stable/20230207/', Recursive=True)
        for page in page_iterator:
            for parameter in page['Parameters']:
                ssm_param = ssm_client.get_parameter(Name=parameter['Name'])
                ami_id = ssm_param['Parameter']['Value']
                image_ids.append(ami_id)
        # choose the ami id based on the architecture
        for instance_type_info in instance_types_info:
            architecture = instance_type_info['ProcessorInfo']['SupportedArchitectures']
            if architecture == ['i386', 'x86_64']:
                ami_id = image_ids[0]
            elif architecture == ['arm64']:
                ami_id = image_ids[1]
        # get the image information
        image_filters = [{'Name': 'image-id', 'Values': [ami_id]}]
        images = ec2_client.describe_images(Filters=image_filters)['Images']
        # launching instance with specified parameters
        user_data = f"""#!/bin/bash
                        sudo echo '{public_key}' >> /home/ubuntu/.ssh/authorized_keys
                        """
        instance_params = {
            'ImageId': images[0]['ImageId'],
            'InstanceType': instance_type,
            'MinCount': 1,
            'MaxCount': 1,
            'UserData': user_data
        }
        response = ec2_client.run_instances(**instance_params)
        instance_id = response['Instances'][0]['InstanceId']
        print(f'Launched instance with ID: {instance_id} in region {region}')
        unique_id = cloud + region + instance_id
        # adding tag to the instance
        ec2_client.create_tags(Resources=[instance_id], Tags=[{'Key': 'Name', 'Value': username}])
        # create connection to the database
        connection = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connection.cursor()
        # extracting public-ip with instanace_id
        ec2 = boto3.client('ec2', region_name=region)
        ec2.get_waiter('instance_running').wait(InstanceIds=[instance_id])
        response = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        # execute insert query to update the database
        insert_query = "INSERT INTO provisioned_vm(UNIQUE_ID, CLOUD, CLD_REGION, ID, TYPE, IP, USERNAME) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        record_tuple = (unique_id, cloud, region, instance_id, vmid, public_ip, username)
        cursor.execute(insert_query, record_tuple)
        connection.commit()
        # close the database connection
        cursor.close()
        connection.close()
        print(f"Database updated with instance ID: {instance_id} in region {region}!")
        return f"Instance Created with ID: {instance_id} in region {region}!\nTo SSH into the instance, run: ssh ubuntu@{public_ip}"
    except Exception as e:
        print(f"Error in aws.py launchvm function: {e}")
        return "500 Internal Server Error"

# function for rebooting instance
def rebootvm(instance_id, region):
    try:
        # creating ec2 client
        ec2 = boto3.client('ec2', region_name=region)
        # rebooting instance with specified id
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f'Rebooting instance with ID: {instance_id}')
        return f"Instance with ID {instance_id} is rebooting."
    except Exception as e:
        print(f"Error in aws.py rebootvm function: {e}")
        return "500 Internal Server Error"

# function for stopping instance
def stopvm(instance_id, region):
    try:
        # creating ec2 client
        ec2 = boto3.client('ec2', region_name=region)        
        # check instance status
        response = ec2.describe_instance_status(InstanceIds=[instance_id])
        if 'InstanceStatuses' in response and response['InstanceStatuses']:
            instance_status = response['InstanceStatuses'][0]['InstanceState']['Name']
            if instance_status == 'stopped':
                return f"Instance with ID {instance_id} is already stopped."
        else:
            return f"Instance with ID {instance_id} is already stopped."
        # stopping instance with specified id
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f'Stopping instance with ID: {instance_id}')
        # wait until the instance is stopped
        waiter = ec2.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[instance_id])
        # removing ip from provisioned_vm table
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connection = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connection.cursor()
        query = f"UPDATE provisioned_vm SET IP=NULL WHERE ID='{instance_id}'"
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        return f"Instance with ID {instance_id} has been stopped."
    except Exception as e:
        print(f"Error in aws.py stopvm function: {e}")
        return "500 Internal Server Error"

# function for starting instance
def startvm(instance_id, region):
    try:
        # creating ec2 client
        ec2 = boto3.client('ec2', region_name=region)
        # check if instance exists
        response = ec2.describe_instances(InstanceIds=[instance_id])
        if 'Reservations' in response and response['Reservations']:
            instance_status = response['Reservations'][0]['Instances'][0]['State']['Name']
            if instance_status == 'running':
                return f"Instance with ID {instance_id} is already running."
        else:
            return f"Instance with ID {instance_id} is not found."
        # starting instance with specified id
        ec2.start_instances(InstanceIds=[instance_id])
        print(f'Starting instance with ID: {instance_id}')
        # waiting for instance to start running
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        # get instance public ip address
        response = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        # updating ip in provisioned_vm table
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        connection = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connection.cursor()
        query = f"UPDATE provisioned_vm SET IP='{public_ip}' WHERE ID='{instance_id}'"
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        return f"Instance with ID {instance_id} is running with IP address {public_ip}."
    except Exception as e:
        print(f"Error in aws.py startvm function: {e}")
        return "500 Internal Server Error"

# function for terminating instance
def terminatevm(instance_id, region):
    try:
        # creating ec2 client
        ec2 = boto3.client('ec2', region_name=region)
        # terminating instance with specified id
        ec2.terminate_instances(InstanceIds=[instance_id])
        print(f'Terminated instance with ID: {instance_id}')
        # updating database with instance details
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        # create connection to the database
        connection = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connection.cursor()
        # execute delete query to update the database
        delete_query = "DELETE FROM provisioned_vm WHERE ID = %s"
        cursor.execute(delete_query, (instance_id,))
        connection.commit()
        # close the database connection
        cursor.close()
        connection.close()
        print(f"Database updated after termination of instance with ID: {instance_id}!")
        return f"Instance with ID: {instance_id} terminated and database updated!"
    except Exception as e:
        print(f"Error in aws.py terminatevm function: {e}")
        return "500 Internal Server Error"
