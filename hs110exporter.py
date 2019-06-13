#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Python 3 to python 2 compatibilty
from __future__ import print_function
from builtins import bytes

from prometheus_client import start_http_server, Gauge
import struct
import time
import socket
import argparse
import json

version = 0.81

keyname = {
    "h1": { # Hardware version 1.x
        "current": "current",
        "voltage": "voltage",
        "power": "power",
        "total": "total"
    },
    "h2": { # Hardware version 2.x
        "current": "current_ma",
        "voltage": "voltage_mv",
        "power": "power_mw",
        "total": "total_wh"
    }
}

# Default HS110 hardware version
hardware = "h2"

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
hs110_key = 171

# Check if IP is valid
def validIP(ip):
    if type(ip) not in [str]:
        raise TypeError("The IP parameter must be a string")

    ip = ip.strip()  # Remove trailing spaces

    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        raise ValueError("Invalid IP Address.")
    return ip

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171

def encrypt(string):
    if type(string) not in [str]:
        raise TypeError("The encrypt parameter must be a string")
    key = hs110_key
    result =  b"\0\0\0" + bytes([len(string)])
    for i in bytes(string.encode('latin-1')):
        a = key ^ i
        key = a
        result += bytes([a])
    return result

def decrypt(string):
    if type(string) not in [bytes]:
        raise TypeError("The decrypt parameter must be bytes")
    string= string[4:]
    key = hs110_key
    result = b""
    for i in bytes(string):
        a = key ^ i
        key = i
        result += bytes([a])
    return result.decode('latin-1')

def get_data(item):
    """ Get item from HS110 array of values """
    allowed_items = ['power', 'current', 'voltage', 'total']
    if type(item) is not str:
        raise TypeError('get_data parameter must be str type')
    if item not in allowed_items:
        raise ValueError('get_data parameter must be one of: [' + ', '.join(allowed_items) + ']')
    try:
        return received_data["emeter"]["get_realtime"][keyname[hardware][item]]
    except socket.error:
        quit("Could not connect to host " + ip + ":" + str(port))
        return 0

# Main entry point
if __name__ == '__main__':
    # Parse commandline arguments
    parser = argparse.ArgumentParser(description="TP-Link Wi-Fi Smart Plug Prometheus exporter v" + str(version))
    parser.add_argument("-t", "--target", metavar="<ip>", required=True, help="Target IP Address", type=validIP)
    parser.add_argument("-f", "--frequency", metavar="<seconds>", required=False, help="Interval in seconds between checking measures", default=1, type=int)
    parser.add_argument("-p", "--port", metavar="<port>", required=False, help="Port for listenin", default=8110, type=int)
    args = parser.parse_args()

    # Set target IP, port and command to send
    ip = args.target
    listen_port = args.port
    sleep_time = args.frequency
    port = 9999
    cmd = '{"emeter":{"get_realtime":{}}}'
    received_data = {
      "emeter": {
        "get_realtime": {
          keyname[hardware]['current']: 0,
          keyname[hardware]['voltage']: 0,
          keyname[hardware]['power']: 0,
          keyname[hardware]['total']: 0,
          "err_code":0
        }
      }
    }

    # Send command and receive reply

    # Create a metric to track time spent and requests made.
    # Gaugage: it goes up and down, snapshot of state

    REQUEST_POWER   = Gauge('hs110_power_watt', 'HS110 Watt measure')
    REQUEST_CURRENT = Gauge('hs110_current', 'HS110 Current measure')
    REQUEST_VOLTAGE = Gauge('hs110_voltage', 'HS110 Voltage measure')
    REQUEST_TOTAL   = Gauge('hs110_total', 'HS110 Energy measure')


    REQUEST_POWER.set_function(lambda: get_data('power'))
    REQUEST_CURRENT.set_function(lambda: get_data('current'))
    REQUEST_VOLTAGE.set_function(lambda: get_data('voltage'))
    REQUEST_TOTAL.set_function(lambda: get_data('total'))

    # Start up the server to expose the metrics.
    start_http_server(listen_port)

    # Main loop
    while True:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(2)

        try:
            sock_tcp.connect((ip, port))
            sock_tcp.send(encrypt(cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()
            # Sample return value received:
            # HS110 Hardware 1: {"emeter":{"get_realtime":{"voltage":229865,"current":1110,"power":231866,"total":228,"err_code":0}}}
            # HS110 Hardware 2: {"emeter":{"get_realtime":{"voltage_mv":229865,"current_ma":1110,"power_mw":231866,"total_wh":228,"err_code":0}}}
            received_data = json.loads(decrypt(data))
            print(received_data)
            if "current_ma" in received_data['emeter']['get_realtime']:
                hardware = "h2"
            else:
                hardware = "h1"
            print("IP: " + ip + ":" + str(port) + " Received power: " + str(received_data["emeter"]["get_realtime"][keyname[hardware]['power']]))
        except socket.error:
            print("Could not connect to the host "+ ip + ":" + str(port))
        except ValueError:
            received_data = {"emeter":{"get_realtime":{keyname[hardware]['voltage']:0,keyname[hardware]['current']:0,keyname[hardware]['power']:0,keyname[hardware]['total']:0,"err_code":0}}}
            print("Could not decrypt data from hs110.")

        time.sleep(sleep_time)

