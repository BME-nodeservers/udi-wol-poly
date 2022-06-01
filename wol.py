#!/usr/bin/env python3
"""
Polyglot v3 node server to create Wake-On-Lan nodes
Copyright (C) 2022 Robert Paauwe

MIT License
"""
import udi_interface
import sys
import time
import re
from wakeonlan import send_magic_packet

LOGGER = udi_interface.LOGGER
polyglot = None
Parameters = None
n_queue = []

'''
WOLNode is a simple node that implements a single command: send WOL
It has no status.
'''
class WOLNode(udi_interface.Node):
    id = 'wol'
    drivers = [
            ]

    def __init__ (self, polyglot, primary, address, name, mac, ip):
        self.poly = polyglot
        self.address = address
        self.name = name
        self.mac = mac
        self.ip = ip
        super(WOLNode, self).__init__(polyglot, primary, address, name)


    def wakeOnLan(self, command):
        LOGGER.info('Sending magic WOL packet to {} ({})'.format(self.mac, self.name))
        try:
            send_magic_packet(self.mac, ip_address=self.ip)
        except Exception as e:
            LOGGER.error('Failed to send WOL packet to {}: {}'.format(self.name, e))

    commands = {'WOL': wakeOnLan}

'''
node_queue() and wait_for_node_event() create a simple way to wait
for a node to be created.  The nodeAdd() API call is asynchronous and
will return before the node is fully created. Using this, we can wait
until it is fully created before we try to use it.
'''
def node_queue(data):
    n_queue.append(data['address'])

def wait_for_node_event():
    while len(n_queue) == 0:
        time.sleep(0.1)
    n_queue.pop()

'''
Read the user entered custom parameters. 
There should be one or more host : mac address parameters
'''
def parameterHandler(params):
    global polyglot

    LOGGER.error('CUSTOMPARAMS handler called {}'.format(params))
    if not params:
        return

    for param in params:
        host = param
        mac = params[param].split('/')[0]
        ip = params[param].split('/')[1]

        #address = polyglot.getValidAddress(mac)
        address = bytes(mac, 'utf-8').decode('utf-8','ignore')
        address = re.sub(r"[<>`~!@#$%^&*(){}[\]?/\\;:\"'\-]+", "", address.lower()[:14])
        if not polyglot.getNode(address):
            node = WOLNode(polyglot, address, address, host, mac, ip)
            polyglot.addNode(node)
            wait_for_node_event()
        else:
            # update mac address
            node = polyglot.getNode(address)
            node.mac = mac

    LOGGER.error('Finished processing custom parameters')


if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start('1.0.2')

        # subscribe to the events we want
        polyglot.subscribe(polyglot.CUSTOMPARAMS, parameterHandler)
        polyglot.subscribe(polyglot.ADDNODEDONE, node_queue)

        # Start running
        polyglot.ready()
        polyglot.setCustomParamsDoc()
        polyglot.updateProfile()

        # Just sit and wait for events
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

