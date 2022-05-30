#!/usr/bin/env python3
"""
Polyglot v3 node server to create Wake-On-Lan nodes
Copyright (C) 2022 Robert Paauwe

MIT License
"""
import udi_interface
import sys
import time

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

    def __init__ (self, polyglot, primary, address, name, mac):
        self.poly = polyglot
        self.address = address
        self.name = name
        self.mac = mac
        super(WOLNode, self).__init__(polyglot, primary, address, name)


    def wakeOnLan(self, command):
        LOGGER.info('Sending magic WOL packet to {} ({})'.format(self.mac, self.name))

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

    for param in params:
        host = param
        mac = params[param]
        address = polyglot.getValidAddress(mac)
        if not polyglot.getNode(address):
            node = WOLNode(polyglot, address, address, host, mac)
            polyglot.addNode(node)
            wait_for_node_event()
        else:
            # update mac address
            node = getNode(address)
            node.mac = mac

    LOGGER.error('Finished processing custom parameters')


if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start('1.0.0')

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
        
