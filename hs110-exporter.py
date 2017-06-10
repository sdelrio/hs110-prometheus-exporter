#!/usr/bin/env python

from prometheus_client import start_http_server, Gauge
import time
import socket
import argparse
import json

version = 0.55

# Check if IP is valid
def validIP(ip):
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        parser.error("Invalid IP Address.")
    return ip

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
def encrypt(string):
    key = 171
    result = "\0\0\0\0"
    for i in string:
        a = key ^ ord(i)
        key = a
        result += chr(a)
    return result

def decrypt(string):
    key = 171
    result = ""
    for i in string:
        a = key ^ ord(i)
        key = ord(i)
        result += chr(a)
    return result

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
received_data = {}

# Send command and receive reply

# Create a metric to track time spent and requests made.
# Gaugage: it goes up and down, snapshot of state

REQUEST_POWER   = Gauge('hs110_power_watt', 'HS110 Watt measure')
REQUEST_CURRENT = Gauge('hs110_current', 'HS110 Current measure')
REQUEST_VOLTAGE = Gauge('hs110_voltage', 'HS110 Voltage measure')


REQUEST_POWER.set_function(lambda: get_power() )
REQUEST_CURRENT.set_function(lambda: get_current() )
REQUEST_VOLTAGE.set_function(lambda: get_voltage() )

def get_power():
    """ Get HS110 power """
    try:
        return  received_data["emeter"]["get_realtime"]["power"]
    except socket.error:
        quit("Could not connect to host " + ip + ":" + str(port))
        return 0

def get_current():
    """ Get HS110 current """
    try:
        return  received_data["emeter"]["get_realtime"]["current"]
    except socket.error:
        quit("Could not connect to host " + ip + ":" + str(port))
        return 0

def get_voltage():
    """ Get HS110 voltage """
    try:
        return  received_data["emeter"]["get_realtime"]["voltage"]
    except socket.error:
        quit("Could not connect to host " + ip + ":" + str(port))
        return 0

# Main entry point
if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(listen_port)

    # Main loop
    while True:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.connect((ip, port))
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        sock_tcp.close()
        # Sample return value received:
        # {"emeter":{"get_realtime":{"current":1.543330,"voltage":235.627293,"power":348.994080,"total":9.737000,"err_code":0}}}
        received_data = json.loads(decrypt(data[4:]))
        print "IP: " + ip + ":" + str(port) + " Received power: " + str(received_data["emeter"]["get_realtime"]["power"])

        time.sleep(sleep_time)

