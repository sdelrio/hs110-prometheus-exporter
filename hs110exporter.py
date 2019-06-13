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

version = 0.9

def validIP(ip):
    """ Check type format and valid IP for input parameter """
    if type(ip) not in [str]:
        raise TypeError("The IP parameter must be a string")

    ip = ip.strip()  # Remove trailing spaces

    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        raise ValueError("Invalid IP Address.")
    return ip

class HS110data:
    """ Storage and management for HS110 data """
    def __init__(self, hardware_version='h2'):
        """ Constructor for HS110 data
        hardware_version: defaults to 'h2' can also be 'h1' """

        allowed_hardware = ['h1', 'h2']
        if hardware_version in allowed_hardware:
            self.__hardware = hardware_version
        else:
            raise ValueError("hardware_version must be " + ' or '.join(allowed_hardware))

        self.__keyname = {
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

        self.received_data = self.__empty_data()

        # Encryption and Decryption of TP-Link Smart Home Protocol
        # XOR Autokey Cipher with starting key = 171
        self.__hs110_key = 171

    def __encrypt(self, string):
        if type(string) not in [str]:
            raise TypeError("The encrypt parameter must be a string")
        key = self.__hs110_key
        result =  b"\0\0\0" + bytes([len(string)])
        for i in bytes(string.encode('latin-1')):
            a = key ^ i
            key = a
            result += bytes([a])
        return result

    def __decrypt(self, string):
        if type(string) not in [bytes]:
            raise TypeError("The decrypt parameter must be bytes")
        string= string[4:]
        key = self.__hs110_key
        result = b""
        for i in bytes(string):
            a = key ^ i
            key = i
            result += bytes([a])
        return result.decode('latin-1')

    def __str__(self):
        return ', '.join(['{key}={value}'.format(key=key, value=self.received_data['emeter']['get_realtime'].get(key)) for key in self.received_data['emeter']['get_realtime']])

    def __empty_data(self):
        return {
            "emeter": {
                "get_realtime": {
                self.__keyname[self.__hardware]['current']: 0,
                self.__keyname[self.__hardware]['voltage']: 0,
                self.__keyname[self.__hardware]['power']: 0,
                self.__keyname[self.__hardware]['total']: 0,
                "err_code":0
                }
            }
        }

    def receive(self, data):
        """ Receive encrypted data, decrypts and stores into self.reived_data """
        if type(data) is not bytes:
            raise ValueError("receive_data parameter must be of type bytes")
        try:
            self.received_data = json.loads(self.__decrypt(data))
            if "current_ma" in self.received_data['emeter']['get_realtime']:
                self.__hardware = 'h2'
            else:
                self.__hardware = 'h1'
        except:
            raise ValueError("json.loads decrypt data")

    def get_cmd(self):
        """ Get encrypted command to get realtime info from HS110 """
        cmd = '{"emeter":{"get_realtime":{}}}'
        return self.__encrypt(cmd)

    def get_data(self, item):
        """ Get item (power, current, voltage or total) from HS110 array of values """
        allowed_items = ['power', 'current', 'voltage', 'total']
        if type(item) is not str:
            raise TypeError('get_data parameter must be str type')
        if item not in allowed_items:
            raise ValueError('get_data parameter must be one of: [' + ', '.join(allowed_items) + ']')
        try:
            return self.received_data["emeter"]["get_realtime"][self.__keyname[self.__hardware][item]]
        except socket.error:
            quit("Could not connect to host " + ip + ":" + str(port))
            return 0

    def reset_data(self):
        """ Reset self.received_data values to 0 """
        self.received_data = self.__empty_data()

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
    # Init object
    hs110 = HS110data()

    # Send command and receive reply

    # Create a metric to track time spent and requests made.
    # Gaugage: it goes up and down, snapshot of state

    REQUEST_POWER   = Gauge('hs110_power_watt', 'HS110 Watt measure')
    REQUEST_CURRENT = Gauge('hs110_current', 'HS110 Current measure')
    REQUEST_VOLTAGE = Gauge('hs110_voltage', 'HS110 Voltage measure')
    REQUEST_TOTAL   = Gauge('hs110_total', 'HS110 Energy measure')


    REQUEST_POWER.set_function(lambda: hs110.get_data('power'))
    REQUEST_CURRENT.set_function(lambda: hs110.get_data('current'))
    REQUEST_VOLTAGE.set_function(lambda: hs110.get_data('voltage'))
    REQUEST_TOTAL.set_function(lambda: hs110.get_data('total'))

    print("Configuration IP: " + ip + ":" + str(port) )
    print("Initialising with empty data: ",  hs110)
    # Start up the server to expose the metrics.
    start_http_server(listen_port)

    # Main loop
    while True:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(2)

        try:
            sock_tcp.connect((ip, port))
            sock_tcp.send(hs110.get_cmd())
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            # Sample return value received:
            # HS110 Hardware 1: {"emeter":{"get_realtime":{"voltage":229865,"current":1110,"power":231866,"total":228,"err_code":0}}}
            # HS110 Hardware 2: {"emeter":{"get_realtime":{"voltage_mv":229865,"current_ma":1110,"power_mw":231866,"total_wh":228,"err_code":0}}}

            hs110.receive(data)  # Receive and decrypts data
            print(hs110)
        except socket.error:
            print("Could not connect to the host "+ ip + ":" + str(port) + " Keeping last values")
        except ValueError:
            hs110.reset_data()
            print("Could not decrypt data from hs110. Reseting values.")

        time.sleep(sleep_time)

