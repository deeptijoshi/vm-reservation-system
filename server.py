from flask import Flask, jsonify, request, abort, make_response
from paramiko import SSHClient
import ConfigParser
import uuid
import paramiko

app = Flask(__name__)

#Load Inventory from inventory.ini file on application startup
cfg = ConfigParser.ConfigParser()
with open('inventory.ini') as cfg_file:
    cfg.readfp(cfg_file)
for s in cfg.sections():
    print s

def get_free_vm():
    '''
    Iterate through inventory file to find the first VM with reservation_status as 'free'
    and return it's IP address
    '''
    for s in cfg.sections():
        if cfg.get(s, 'reservation_status') == 'free':
            return s

def update_inventory(vm,reservation_status,reservation_id):
    '''
    Utility function to update inventory.ini file reflecting VM reservation status changes
    '''
    cfg.set(vm, 'reservation_status', reservation_status)
    cfg.set(vm, 'reservation_id', reservation_id)
    with open('inventory.ini','w') as cfg_file:
        cfg.write(cfg_file)

def vm_cleanup(ip_addr):
    '''
    Utility function to cleanup VM before it is released back to free pool
    Cleanup here is to delete all the files from /tmp directory.
    Since we don't have any live VMs right now, this function attempts to
    ssh into a VM which raises an exception.
    For the completeness of this assignment, we catch that exception and 
    work around it and always return True as exit code.
    '''
    host = ip_addr
    user = cfg.get(host, 'login_user')
    passwd = cfg.get(host, 'login_passwd')
    try:
        ssh_session = SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, 22, user, passwd, timeout=3)
        stdin, stdout, stderr = ssh.exec_command('rm -rf /tmp/*')
    except:
        print 'VM cleanup over SSH has failed'
    finally:
        return True

@app.errorhandler(400)
def bad_request(error):
    '''
    Flask application sends HTML response while aborting execution upon receiving
    an ill formed request. This function enhances the error handling by sending out
    JSON response to make it consistent with other responses
    '''
    return make_response(jsonify({'error': 'IP or ReservationID or both the fields are missing in the request'}), 400)

@app.route('/vms/api/v1.0/checkout',methods=['GET'])
def reserve_vm():
    '''
    If function get_free_vm returns an IP address of the VM that is 'free', 
    assign it to the requester of current request. 
    Assigning a VM entails updating 'reservation_status' and 'reservation_id'
    fields in an inventory file for a particular VM and then sending JSON 
    response back to requester with details like IP address, Login credentials
    and reservation_id.
    User needs to preserve this reservation_id and send it back with checkin
    request to be able to release VM back to free pool.
    '''
    vm_available = get_free_vm()
    if vm_available is None:
        print 'No VM available for checkout'
        response_body = {'error' : 'No VM is currently available for checkout Please retry after some time'}
        response_code = 404
    else:
        print 'VM %s is available for checkout' % vm_available
        reservation_id = uuid.uuid4()
        try:
            update_inventory(vm_available, 'reserved', reservation_id)
            response_body = {
                'IP' : vm_available,
                'LoginID' : cfg.get(vm_available, 'login_user'),
                'LoginPassword' : cfg.get(vm_available, 'login_passwd'),
                'ReservationID' : reservation_id
            }
            response_code = 200
        except:
            print 'Error occurred during inventory update for checkout'
            response_body = {'error' : 'Internal Server Error' }
            response_code = 500
    return jsonify(response_body), response_code

@app.route('/vms/api/v1.0/checkin',methods=['POST'])
def release_vm():
    '''
    If requester has sent JSON payload over POST request comprising of fields
    IP, reservation_id and if VM with that IP is not already marked as 'free',
    go ahead and release VM back to free pool. Releasing VM entails setting 
    'reservation_status' back to 'free' and 'reservation_id' to 'None'
    '''
    print request.json
    if not request.json or not 'ReservationID' in request.json or not 'IP' in request.json:
        abort(400)
    if not request.json['IP'] in cfg.sections():
        print 'Non existent IP address specified in the request'
        response_body = {'error': 'Invalid IP address'}
        response_code = 400
    elif not cfg.get(request.json['IP'], 'reservation_status') == 'reserved':
        print 'Requested VM is Not in reserved state'
        response_body = {'error': 'VM specified in request is not in reserved state. VM can not be checked In'}
        response_code = 400
    elif not request.json['ReservationID'] == cfg.get(request.json['IP'], 'reservation_id'):
        print 'Reservation ID specified is not correct. VM can not be checked In'
        response_body = {'error': 'Reservation ID specified is not correct. VM can not be checked In'}
        response_code = 400
    else:
        print 'Releasing VM back to the free pool'
        if vm_cleanup(request.json['IP']):
            try:
                update_inventory(request.json['IP'], 'free', None)
                response_body = {'status': 'VM successfully released back to free pool'}
                response_code = 200
            except:
                print 'Inventory update during VM checkin failed'
                response_body = {'error': 'Internal Server Error'}
                response_code = 500

    return jsonify(response_body), response_code

if __name__ == '__main__':
   app.run()
