![logo](https://github.com/9846381903/cloudash/assets/90718392/9c40ef18-a096-4fb7-b3b0-fb4a7f9d1701)

# Cloudash: Optimal VM Deployment Solution

Cloudash streamlines the task of selecting and launching virtual machines (VMs) on popular cloud providers such as AWS and Azure. By leveraging real-time pricing data, Cloudash ensures users deploy VMs that are both cost-effective and aligned with their computational requirements.

## Table of Contents

- [Project Description](#project-description)
- [Prerequisites](#prerequisites)
- [System Components Overview](#system-components-overview)
- [Architecture Diagram](#architecture-diagram)
- [Database Schema](#database-schema)

## Project Description

Designed with simplicity in mind, Cloudash abstracts away the complexities of cloud pricing models. Whether a user is searching for a specific RAM and CPU combination or looking for the most affordable VM available, Cloudash offers a seamless solution. Its intelligent backend constantly updates itself with the latest VM pricing from renowned providers, ensuring users always get the best deals.

## Prerequisites

- AWS cloud with all regions enabled.
- Azure cloud (Note: You may need to contact customer care to enable all regions in the Azure cloud for the Virtual Machines service).

## System Components Overview

### vm_inventory:

This module handles the VM pricing information for different cloud providers. It's designed to:

- Regularly pull VM pricing data from providers like AWS, Azure, etc.
- Update the database with the latest pricing information.
- Run as a cron job to ensure prices remain up-to-date.

### inventory_api:

Once users specify their desired VM resources, this API:

- Queries the vm_inventory to fetch the best VM options.
- Provides a ranked list of VMs based on cost and matching the given specifications (CPU & RAM).

### aws_operation & azure_operation:

These are the connectors or interfaces to AWS and Azure, respectively. Their functionalities include:

- Launching VMs based on user requirements.
- Updating the database with the current state of VMs (e.g., running, stopped, terminated).
- Handling cloud-specific exceptions or nuances in VM management.

### user:

Focused on user management, this module:

- Manages user registrations.
- Handles user logins and authentication.
- Provides security checks and validation to ensure data integrity.

### intelligent_controller:

Serving as the main gateway for all operations, this controller:

- Routes incoming requests to the appropriate service.
- Performs initial validation on user requests.
- Acts as an intermediary between the frontend and other backend components, ensuring efficient communication.

## Architecture Diagram

![archetecture](https://github.com/9846381903/cloudash/assets/90718392/7c2af1bc-c49d-41f8-a740-161e53817535)

## Database Schema

![database](https://github.com/9846381903/cloudash/assets/90718392/b0ea03ae-f65e-4541-b3a2-6938e3686a9b)
