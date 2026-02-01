"""
Modem Emulator
Hackathon Demo Edition - English Version
"""

import vensasim_emulator

def send_apdu_to_vensasim(command_apdu, silent=False):
    """Send APDU command to VensaSIM and get response"""
    response = vensasim_emulator.process_apdu(command_apdu, silent)
    return response

def relay_to_network(data):
    """Relay data to network (stub)"""
    return data

def receive_from_network(data):
    """Receive data from network (stub)"""
    return data
