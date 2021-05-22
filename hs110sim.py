#!/usr/bin/env python3
import socket
import sys

from os import environ
from random import randrange
from hs110exporter import HS110data


bind_IP = '0.0.0.0'
bind_PORT = 9999

def generate_data_random() -> str:
    """ Generate hs110 data """

    current = randrange(300, 400)/1000  # 0.342122
    voltage = randrange(210000, 240000)/1000 # 239.527888
    power   = current * voltage
    total   = randrange(10000, 20000)/1000  #10.155000

    data = '{"emeter":{"get_realtime":{"current_ma":' \
            + str(current) \
            + ',"voltage_mv":' \
            + str(voltage) \
            + ',"power_mw":' \
            + str(power) \
            + ',"total_wh":' \
            + str(total) \
            + ',"err_code":0}}}'

    return h._HS110data__encrypt(data)

if (environ.get('HW_VERSION') == '2'):
    hw_version = 2
    h = HS110data(hardware_version='h2')
else:
    hw_version = 1
    h = HS110data(hardware_version='h1')

print("[info] HW version: %s" % hw_version)
print("[info] Watching on %s:%s" % (bind_IP, bind_PORT))

my_socket = socket.socket()
my_socket.bind((bind_IP, bind_PORT))
my_socket.listen(5)

print("[info] HS110sim started...")

while True:
    conexion = None
    try:
        conexion, addr = my_socket.accept()
        print("[address/port]: " + str(addr))

        peticion = conexion.recv(1024)
        if not peticion:
            break

        new_data = generate_data_random()
        conexion.send(new_data)
        conexion.close()

        print("[recv]: " + h._HS110data__decrypt(peticion))
        print("[send]: " + h._HS110data__decrypt(new_data))

    except IOError as msg:
        print(msg)
        continue
    except KeyboardInterrupt:
        if conexion:
            conexion.close()
        print("[exit]: Keyboard interrupt detected")
        break
    except Exception as e:
        print('[error]: line: {}'.format(sys.exc_info()[-1].tb_lineno))
        print('[error]: type:', type(e).__name__)
        print('[error]: desc:', e)
        continue

my_socket.shutdown(0)
my_socket.close()
