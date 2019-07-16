#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dpcontracts import require, ensure
from prometheus_client import start_http_server, Gauge
import struct
import time
import socket
import argparse
import json

version = 0.94

@require("ip must be a string", lambda args: isinstance(args.ip, str))
@require("ip must not be empty", lambda args: len(args.ip) > 0)
@ensure("result is part of input", lambda args, result: result in args.ip )
def validIP(ip: str) -> str:
    """ Check type format and valid IP for input parameter """

    ip = ip.strip()  # Remove trailing spaces

    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        raise ValueError("Invalid IP Address %s" % ip)
    return ip

class HS110data:
    """ Storage and management for HS110 data """
    @require("ip must be a valid IP", lambda args: validIP(args.ip))
    @require("hardware_version must be string", lambda args: isinstance(args.hardware_version, str))
    @require("hardware_version must be 'h1' or 'h2' ", lambda args: args.hardware_version in ['h1', 'h2'])
    @require("port must be intenger", lambda args: isinstance(args.port, int) and args.port >= 0 and args.port <= 65535)
    def __init__(self, hardware_version: str='h2', ip: str='192.168.1.53', port: int=9999):
        """ Constructor for HS110 data
        hardware_version: defaults to 'h2' can also be 'h1' 
        port: hss110 target port, for h1 and h2 is 9999,
        """
        self.__hardware = hardware_version

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

        self.__received_data = self.__empty_data()

        # Encryption and Decryption of TP-Link Smart Home Protocol
        # XOR Autokey Cipher with starting key = 171
        self.__hs110_key = 171

        # HS110 address and port
        self.__ip = ip
        self.__port = port

    @require("The encrypt parameter must be str type", lambda args: isinstance(args.string, str))
    @require("String must not be empty", lambda args: len(args.string) > 0)
    @ensure("Result must be bytes", lambda args, result: isinstance(result, bytes))
    def __encrypt(self, string: str) -> bytes:
        """ Encrypts string to send to HS110 """
        key = self.__hs110_key
        result =  b"\0\0\0" + bytes([len(string)])
        for i in bytes(string.encode('latin-1', 'replace')):
            a = key ^ i
            key = a
            result += bytes([a])
        return result

    @require("The decrypt parameter must be bytes type", lambda args: isinstance(args.data, bytes))
    @require("Parameter must have more than 3 bytes starting with 000", lambda args: len(args.data) > 3 and args.data[0:3] == b"\0\0\0")
    @ensure("Result must be str", lambda args, result: isinstance(result, str))
    def __decrypt(self, data: bytes) -> str:
        """ Decrypts bytestring received by HS110 """
        data= data[4:]
        key = self.__hs110_key
        result = b""
        for i in bytes(data):
            a = key ^ i
            key = i
            result += bytes([a])
        return result.decode('latin-1', 'replace')

    def __str__(self) -> str:
        """ Prints content of received HS110 data """
        return ', '.join(['{key}={value}'.format(key=key, value=self.__received_data['emeter']['get_realtime'].get(key)) for key in self.__received_data['emeter']['get_realtime']])

    def __empty_data(self) -> dict:
        """ Clear received data to 0 values """
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

    @require("Parameter data must be bytes type", lambda args: isinstance(args.data, bytes))
    @require("Parameter must have more than 3 bytes starting with 000", lambda args: len(args.data) > 3 and args.data[0:3] == b"\0\0\0")
    def receive(self, data: bytes):
        """ Receive encrypted data, decrypts and stores into self.reived_data """
        try:
            self.__received_data = json.loads(self.__decrypt(data))
        except:
            raise ValueError("json.loads decrypt data")

        if "current_ma" in self.__received_data['emeter']['get_realtime']:
            self.__hardware = 'h2'
        else:
            self.__hardware = 'h1'

    def get_cmd(self) -> bytes:
        """ Get encrypted command to get realtime info from HS110 """
        cmd = '{"emeter":{"get_realtime":{}}}'
        return self.__encrypt(cmd)

    @require("Parameter data must be str type", lambda args: isinstance(args.item, str))
    @ensure("Result must be a float or int", lambda args, result: isinstance(result, float) or isinstance(result, int)  )
    def get_data(self, item: str):
        """ Get item (power, current, voltage or total) from HS110 array of values """
        try:
            return float(self.__received_data["emeter"]["get_realtime"][self.__keyname[self.__hardware][item]])
        except KeyError:
            raise KeyError('get_data parameter must be one of: [' + ', '.join(self.__received_data["emeter"]["get_realtime"].keys()) + ']')

    @ensure("Result must be a string", lambda args, result: isinstance(result, str)  )
    def get_connection_info(self):
        return 'HS110 connection: %s:%s' % (self.__ip, str(self.__port))

    def reset_data(self):
        """ Reset self.__received_data values to 0 """
        self.__received_data = self.__empty_data()

    def connect(self):
        """ Connect to hss110 with get command to receive metrics """
        self.send(self.get_cmd())

    def send(self, command):
        """ Send command to hs110 and receive data """
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.settimeout(2)
        try:
            sock_tcp.connect((self.__ip, self.__port))
            sock_tcp.send(command)
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            # Sample return value received:
            # HS110 Hardware 1: {"emeter":{"get_realtime":{"voltage":229865,"current":1110,"power":231866,"total":228,"err_code":0}}}
            # HS110 Hardware 2: {"emeter":{"get_realtime":{"voltage_mv":229865,"current_ma":1110,"power_mw":231866,"total_wh":228,"err_code":0}}}

            self.receive(data)  # Receive and decrypts data
        except socket.error:
            print("[error] Could not connect to the host "+ self.__ip + ":" + str(self.__port) + " Keeping last values")
        except ValueError:
            self.reset_data()
            print("[warning] Could not decrypt data from hs110. Reseting values.")

# Main entry point
if __name__ == '__main__':
    # Parse commandline arguments
    parser = argparse.ArgumentParser(description="TP-Link Wi-Fi Smart Plug Prometheus exporter v" + str(version))
    parser.add_argument("-t", "--target", metavar="<ip>", required=True, help="Target IP Address", type=validIP)
    parser.add_argument("-f", "--frequency", metavar="<seconds>", required=False, help="Interval in seconds between checking measures", default=1, type=int)
    parser.add_argument("-p", "--port", metavar="<port>", required=False, help="Port for listenin", default=8110, type=int)
    args = parser.parse_args()

    # Init object
    hs110 = HS110data(hardware_version='h2', ip=args.target)

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

    print('[info] %s' % hs110.get_connection_info())

    # Start up the server to expose the metrics.
    start_http_server(args.port)
    print("[info] Exporter listenting on TCP: " + str(args.port) )

    # Main loop
    while True:
        hs110.connect()
        print('[info] %s' % hs110)
        time.sleep(args.frequency)
