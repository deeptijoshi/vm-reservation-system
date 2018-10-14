# vm-reservation-system

### Problem Statement:
#### Design and Implement a Virtual Machine reservation system in Python

>Assume you are the administrator of a cloud which hosts some finite number of Virtual Machines. Users of your cloud can borrow or check-out VMs for use. Once they are done using it, they can check-in the VM back. Once a VM is checked in, as an administrator, you should perform some cleanup on the VM and then return it back to the pool of VMs. 

>Implement a system that will allow your clients to check-out and check-in VMs and help you administer usage of VMs in your cloud.

>- When clients need a VM for use, they will call a checkout method provided by your VM reservation system. They should get the IP of a VM they can use, along with any other details you may need.

>- When clients are done using the VM, they will call a checkin method provided by your VM reservation system. 

>- For the sake of this assignment, you can assume cleanup of a VM means that your system will ssh into the VM using its IP and clean up all files in the /tmp directory.

>- After a VM has been cleaned up, your system should add it back to the pool of VMs available for checkout by clients. 

>- If a client requests a VM and no VM is available to be checked out, then your system should let your clients know accordingly, so they may retry after some time.

>- The same VM cannot be checked out by two clients at the same time. 

>- A VM checked out by one client cannot be checked in by some other client. 

>- If your system stops running for some reason and needs to be restarted, then it should continue to know all the information about VMs that have been already checked out and VMs that are available. 


## Solution

### Design Details
This python application implements following two REST API endpoints to manage VM resources in the inventory

To let users checkout VMs for their use:
- /vms/api/v1.0/checkout [GET]

To let users release VMs back to the pool once they are done with their usage
- /vms/api/v1.0/checkin [POST]


These endpoints manage inventory of VMs which is maintained in an INI file **inventory.ini**
VMs are managed with following attributes:

- **IP** (IP address of the VM)
- **reservation_status** (free or reserved)
- **reservation_id** (reservation_id that must be passed along with request to release a VM back to pool. This would only be available to user who checked out the VM and hence thus it protects VM from getting released back to pool without owner's knowledge.
- **login_user**
- **login_passwd**


### How to run this server

```
1. git clone https://github.com/mkamlesh/vm-reservation-system.git
2. virtualenv vm-reservation-system
3. cd vm-reservation-system
4. source bin/activate
5. pip install -U pip
6. pip install -r requirements.txt
7. python server.py
```

### Sample queries to work with this system

1. To checkout a VM
``` 
curl -XGET 'http://localhost:5000/vms/api/v1.0/checkout'
{
  "IP": "192.168.0.2",
  "LoginID": "user2",
  "LoginPassword": "password2",
  "ReservationID": "883dc1d5-6ee3-4b2a-85bb-d3b7cee4bedd"
}
```
Please make sure to take a note of ReservationID mentioned in the response.

2. To release VM back to free pool
```
curl -H "Content-Type: application/json" -X POST -d '{"IP" : "192.168.0.2" "ReservationID" : "883dc1d5-6ee3-4b2a-85bb-d3b7cee4bedd"}' 'http://localhost:5000/vms/api/v1.0/checkin'
{
  "status": "VM successfully released back to free pool"
}


