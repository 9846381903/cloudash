# importing binaries
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption
from azure.core.exceptions import HttpResponseError
import mysql.connector as c
import hashlib
import random
import string

# function for launching instance
def launchvm(username, public_key, vmid, cloud, region, instance_type):
    try:
        # setting up the database
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        # create connection to the database
        connect = c.connect(host=host, user=user, password=password)
        cursor = connect.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS clouddash")
        connect = c.connect(host=host, user=user, password=password, database='clouddash')
        cursor = connect.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS provisioned_vm(UNIQUE_ID VARCHAR(100), CLOUD VARCHAR(100), CLD_REGION VARCHAR(100), ID VARCHAR(100), TYPE VARCHAR(100), IP VARCHAR(100), USERNAME VARCHAR(100))")
        # creating a token for adding to the username value
        word = username
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        salted_word = word + salt
        token = hashlib.sha256(salted_word.encode()).hexdigest()
        short_token = token[:10]
        # azure credentials
        SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
        RESOURCE_GROUP_NAME = 'clouddash'
        VM_NAME = username + short_token
        SSH_PUBLIC_KEY = public_key
        PUBLIC_IP_NAME = VM_NAME
        REGION_CODE = region
        # initialize management clients
        credential = DefaultAzureCredential()
        resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
        compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
        network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)
        # get resource group
        resource_group = resource_client.resource_groups.get(RESOURCE_GROUP_NAME)
        # get vent and subnet names based on region
        vnet_name = f"clouddash-{region}"
        subnet_name = "default"
        # get the existing nsg associated with the vnet
        subnet = network_client.subnets.get(RESOURCE_GROUP_NAME, vnet_name, subnet_name)
        nsg_id = subnet.network_security_group.id
        # get the nsg name from the id
        nsg_name = nsg_id.split('/')[-1]
        # get the nsg object
        nsg = network_client.network_security_groups.get(RESOURCE_GROUP_NAME, nsg_name)
        # create the public ip address if it doesn't exist
        try:
            public_ip_address = network_client.public_ip_addresses.get(RESOURCE_GROUP_NAME, PUBLIC_IP_NAME)
        except HttpResponseError:
            public_ip_parameters = {
                "location": REGION_CODE,
                "public_ip_allocation_method": "Dynamic"
            }
            public_ip_address = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
                                                                                          PUBLIC_IP_NAME,
                                                                                          public_ip_parameters).result()
        # create network interface
        creation_result_nic = network_client.network_interfaces.begin_create_or_update(
            RESOURCE_GROUP_NAME,
            username + short_token + "_nic",
            {
                "location": REGION_CODE,
                "ip_configurations": [{
                    "name": "ip_config",
                    "subnet": {
                        "id": subnet.id
                    },
                    "public_ip_address": {
                        "id": public_ip_address.id
                    }
                }],
                "network_security_group": {
                    "id": nsg.id
                }
            }
        )
        nic = creation_result_nic.result()
        # create vm
        creation_result_vm = compute_client.virtual_machines.begin_create_or_update(
            RESOURCE_GROUP_NAME,
            VM_NAME,
            {
                "location": REGION_CODE,
                "storage_profile": {
                    "image_reference": {
                        "publisher": "Canonical",
                        "offer": "UbuntuServer",
                        "sku": "18.04-LTS",  
                        "version": "latest"
                    }
                },
                "hardware_profile": {
                    "vm_size": instance_type
                },
                "os_profile": {
                    "computer_name": VM_NAME,
                    "admin_username": "ubuntu",
                    "linux_configuration": {
                        "disable_password_authentication": True,
                        "ssh": {
                            "public_keys": [{
                                "path": f"/home/ubuntu/.ssh/authorized_keys",
                                "key_data": SSH_PUBLIC_KEY
                            }]
                        }
                    }
                },
                "network_profile": {
                    "network_interfaces": [{
                        "id": nic.id,
                    }]
                }
            }
        )
        vm = creation_result_vm.result()
        # fetch the public ip address of the launched vm
        public_ip_address = network_client.public_ip_addresses.get(RESOURCE_GROUP_NAME, PUBLIC_IP_NAME).ip_address
        # fetch vmid
        compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
        vm = compute_client.virtual_machines.get(RESOURCE_GROUP_NAME, VM_NAME)
        instance_id = vm.vm_id
        # setting unique_id
        unique_id = cloud + region + instance_id
        # execute insert query to update the database
        insert_query = "INSERT INTO provisioned_vm(UNIQUE_ID, CLOUD, CLD_REGION, ID, TYPE, IP, USERNAME) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        record_tuple = (unique_id, cloud, region, instance_id, vmid, public_ip_address, username)
        cursor.execute(insert_query, record_tuple)
        connect.commit()
        # close the database connection
        cursor.close()
        connect.close()
        print(f"Database updated with instance ID: {instance_id} in region {region}!")
        return f"Instance Created with ID: {instance_id} in region {region}!\nTo SSH into the instance, run: ssh ubuntu@{public_ip_address}"
    except Exception as e:
        print(f"Error in az.py launchvm function: {e}")
        return "500 Internal Server Error"

# function for rebooting vm
def rebootvm(instance_id, region_code):
    try:
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        resource_group_name = "clouddash"
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        vm_name = None
        for vm in compute_client.virtual_machines.list_all():
            if vm.vm_id == instance_id and vm.location == region_code:
                vm_name = vm.name
                break
        if vm_name is not None:
            restart_op = compute_client.virtual_machines.begin_restart(resource_group_name, vm_name)
            restart_op.result()
            return f"Instance with ID {instance_id} is rebooting."
    except Exception as e:
        print(f"Error in az.py rebootvm function: {e}")
        return "500 Internal Server Error"
        
# function for stopping vm
def stopvm(instance_id, region_code):
    try:
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        resource_group_name = "clouddash"
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        vm_name = None
        for vm in compute_client.virtual_machines.list_all():
            if vm.vm_id == instance_id and vm.location == region_code:
                vm_name = vm.name
                break
        if vm_name is not None:
            vm_status = compute_client.virtual_machines.get(resource_group_name, vm_name, expand='instanceView').instance_view.statuses
            # checking the current state of vm
            if any(status.code == "PowerState/running" for status in vm_status):
                stop_op = compute_client.virtual_machines.begin_deallocate(resource_group_name, vm_name)
                stop_op.result()
            else:
                return f"Instance with ID {instance_id} is already stopped."
            print(f'Stopping instance with ID: {instance_id}')
            # updating ip in provisioned_vm table
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
            return f"Instance with ID {instance_id} is stopping."
    except Exception as e:
        print(f"Error in az.py stopvm function: {e}")
        return "500 Internal Server Error"

# function for starting vm
def startvm(instance_id, region_code):
    try:
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        resource_group_name = "clouddash"
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        network_client = NetworkManagementClient(credential, subscription_id)
        vm_name = None
        for vm in compute_client.virtual_machines.list_all():
            if vm.vm_id == instance_id and vm.location == region_code:
                vm_name = vm.name
                break
        if vm_name is not None:
            vm_status = compute_client.virtual_machines.get(resource_group_name, vm_name,
                                                            expand='instanceView').instance_view.statuses
            # checking the current state of VM
            if any(status.code == "PowerState/deallocated" for status in vm_status):
                start_op = compute_client.virtual_machines.begin_start(resource_group_name, vm_name)
                start_op.result()
            else:
                return f"Instance with ID {instance_id} is already running."
            print(f'Starting instance with ID: {instance_id}')
            # updating ip in provisioned_vm table
            host = os.environ.get('DB_HOST')
            user = os.environ.get('DB_USER')
            password = os.environ.get('DB_PASSWORD')
            connection = c.connect(host=host, user=user, password=password, database='clouddash')
            cursor = connection.cursor()
            # getting ipv4 address
            vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
            network_interface_reference = vm.network_profile.network_interfaces[0]
            network_interface_id = network_interface_reference.id.split('/')[-1]
            network_interface = network_client.network_interfaces.get(resource_group_name, network_interface_id)
            ip_config = network_interface.ip_configurations[0]
            public_ip_reference = ip_config.public_ip_address
            public_ip_id = public_ip_reference.id.split('/')[-1]
            public_ip = network_client.public_ip_addresses.get(resource_group_name, public_ip_id)
            ip_address = public_ip.ip_address
            query = f"UPDATE provisioned_vm SET IP='{ip_address}' WHERE ID='{instance_id}'"
            cursor.execute(query)
            connection.commit()
            cursor.close()
            connection.close()
            return f"Instance with ID {instance_id} is starting."
    except Exception as e:
        print(f"Error in az.py startvm function: {e}")
        return "500 Internal Server Error"

# function for terminating vm
def terminatevm(instance_id, region_code):
    try:
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        resource_group_name = "clouddash"
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        network_client = NetworkManagementClient(credential, subscription_id)
        vm_name = None
        for vm in compute_client.virtual_machines.list_all():
            if vm.vm_id == instance_id and vm.location == region_code:
                vm_name = vm.name
                break
        if vm_name is not None:
            vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
            nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
            nic = network_client.network_interfaces.get(resource_group_name, nic_name)
            public_ip_name = None
            if nic.ip_configurations:
                public_ip_id = nic.ip_configurations[0].public_ip_address.id
                public_ip_name = public_ip_id.split('/')[-1]
            # Get disk name
            disk_name = vm.storage_profile.os_disk.name
            # deleting the vm
            delete_op = compute_client.virtual_machines.begin_delete(resource_group_name, vm_name)
            delete_op.wait()
            # deleting the nic
            delete_nic_op = network_client.network_interfaces.begin_delete(resource_group_name, nic_name)
            delete_nic_op.wait()
            # deleting the public ip
            if public_ip_name:
                delete_public_ip_op = network_client.public_ip_addresses.begin_delete(resource_group_name, vm_name)
                delete_public_ip_op.wait()
            # deleting the disk
            delete_disk_op = compute_client.disks.begin_delete(resource_group_name, disk_name)  
            delete_disk_op.wait()  
            print(f'Terminating instance with ID: {instance_id}')
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
        print(f"Error in az.py terminatevm function: {e}")
        return "500 Internal Server Error"

