#!/usr/bin/env python3

import unittest
import socket
import time
import argparse

from unittest.mock import patch, call, MagicMock  # Python 3

from dpcontracts import require, ensure, PreconditionError
from hypothesis import given, assume, example
from hypothesis.strategies import integers, one_of, floats, text, lists, none, permutations, complex_numbers
from hs110exporter import validIP, HS110data, socket, main

class TestValidIP(unittest.TestCase):
  def test_ipstring(self):
    self.assertEqual(validIP('192.168.0.1'), '192.168.0.1')
    self.assertEqual(validIP(' 192.168.0.1 '), '192.168.0.1')

  @given(none())
  @example(b'\x00')
  @example(100)
  @example(100.1)
  @example(3j)
  @example({"string into dict"})
  @example(set("string into set"))
  def test_ipstring_types(self, fake_ip_type):
    self.assertRaises(PreconditionError, validIP, fake_ip_type)

#  @given(text())
#  @example("192.168.0.1.a")
#  @example("192.168.0.1.256")
  def test_ipvalues(self):
    self.assertRaises(ValueError, validIP, "192.168.0.a")

  @given(integers(min_value=1, max_value=255),
    integers(min_value=1, max_value=255),
    integers(min_value=1, max_value=255),
    integers(min_value=1, max_value=255)
  )
  def test_ipvalues_hypo(self, a, b, c, d):
    ip_string = "%s.%s.%s.%s" % (str(a), str(b), str(c), str(d))
    ip_string == validIP(ip_string) 

  @given(integers(min_value=-1000, max_value=1000))
  def test_ipvalues_hypo_raises(self, a):
    if (a < 0 or a > 255):
      ip_string = "%s.%s.%s.%s" % (str(a), str(0), str(1), str(2))
      self.assertRaises(ValueError, validIP, ip_string)

class TestHS110data(unittest.TestCase):
  def test_encryptstring(self):
    hs110 = HS110data()
    text_encrypted = b'\x00\x00\x00\x10\xd0\xf0\x98\xfd\x91\xfd\x92\xa8\x88\xff\x90\xe2\x8e\xea\xca\xb7'
    text_decrypted = '{ hello: world }'

    self.assertEqual(hs110._HS110data__encrypt(text_decrypted), text_encrypted)
    self.assertEqual(hs110._HS110data__decrypt(text_encrypted), text_decrypted)

  @given( one_of(
    floats(),
    none(),
    text()
  ))
  @example(b'\x00\x00\x00\x10')
  @example(100)
  @example(3j)
  @example({"10.1.1.1"})
  @example(set("10.1.1.1"))
  def test_encryptvalues(self, sample_type):
    hs110 = HS110data()
    if (isinstance(sample_type, str) and len(sample_type) > 0):
      self.assertIsInstance(hs110._HS110data__encrypt(sample_type), bytes)
    else:
      self.assertRaises(PreconditionError, hs110._HS110data__encrypt, sample_type)

  @given(none())
  @example(b'\x00\x00\x00\x10')
  @example(100)
  @example(100.1)
  @example(3j)
  @example({"10.1.1.1"})
  @example(set("10.1.1.1"))
  @example("Hello world")
  def test_decryptvalues(self, data):
    hs110 = HS110data()
    if (isinstance(data,bytes) and data[0:3] == b"\0\0\0"):
      self.assertIsInstance(hs110._HS110data__decrypt(data), str)
    else:
      self.assertRaises(PreconditionError, hs110._HS110data__decrypt, data)

  @given(one_of(
    none(),
    text())
  )
  @example(100)
  @example(100.1)
  @example(3j)
  @example('power')
  @example('current')
  @example('voltage')
  @example('total')
  def test_received_data(self, data_item):
    for h in ['h1', 'h2']:
      hs110 = HS110data(h)
      if data_item in ['power', 'current', 'voltage', 'total']:
        self.assertEqual(hs110.get_data(data_item), 0)
      elif isinstance(data_item,str):
        self.assertRaises(KeyError, hs110.get_data, data_item)
      else:
        self.assertRaises(PreconditionError, hs110.get_data, data_item)

  def test_receive(self):
    # current=0.342122, voltage=239.527888, power=66.941523, total=10.155, err_code=0
    sample_data_ok = b'\x00\x00\x00v\xd0\xf2\x97\xfa\x9f\xeb\x8e\xfc\xde\xe4\x9f\xbd\xda\xbf\xcb\x94\xe6\x83\xe2\x8e\xfa\x93\xfe\x9b\xb9\x83\xf8\xda\xb9\xcc\xbe\xcc\xa9\xc7\xb3\x91\xab\x9b\xb5\x86\xb2\x80\xb1\x83\xb1\x9d\xbf\xc9\xa6\xca\xbe\xdf\xb8\xdd\xff\xc5\xf7\xc4\xfd\xd3\xe6\xd4\xe3\xdb\xe3\xdb\xf7\xd5\xa5\xca\xbd\xd8\xaa\x88\xb2\x84\xb2\x9c\xa5\x91\xa0\x95\xa7\x94\xb8\x9a\xee\x81\xf5\x94\xf8\xda\xe0\xd1\xe1\xcf\xfe\xcb\xfe\xce\xfe\xce\xe2\xc0\xa5\xd7\xa5\xfa\x99\xf6\x92\xf7\xd5\xef\xdf\xa2\xdf\xa2'
    sample_data_fail = b'\x00\x00\x00v\xd0\xf2\x97\xfa'

    #  '{"emeter":{"get_realtime":{"current_ma":0.342122,"voltage_mv":239.527888,"power_mw":66.941523,"total_wh":10.155000,"err_code":0}}}'
    sample_data_h2 = b'\x00\x00\x00\x82\xd0\xf2\x97\xfa\x9f\xeb\x8e\xfc\xde\xe4\x9f\xbd\xda\xbf\xcb\x94\xe6\x83\xe2\x8e\xfa\x93\xfe\x9b\xb9\x83\xf8\xda\xb9\xcc\xbe\xcc\xa9\xc7\xb3\xec\x81\xe0\xc2\xf8\xc8\xe6\xd5\xe1\xd3\xe2\xd0\xe2\xce\xec\x9a\xf5\x99\xed\x8c\xeb\x8e\xd1\xbc\xca\xe8\xd2\xe0\xd3\xea\xc4\xf1\xc3\xf4\xcc\xf4\xcc\xe0\xc2\xb2\xdd\xaa\xcf\xbd\xe2\x8f\xf8\xda\xe0\xd6\xe0\xce\xf7\xc3\xf2\xc7\xf5\xc6\xea\xc8\xbc\xd3\xa7\xc6\xaa\xf5\x82\xea\xc8\xf2\xc3\xf3\xdd\xec\xd9\xec\xdc\xec\xdc\xf0\xd2\xb7\xc5\xb7\xe8\x8b\xe4\x80\xe5\xc7\xfd\xcd\xb0\xcd\xb0'
    hs110 = HS110data()

    self.assertRaises(PreconditionError, hs110.receive, 'this is a string')
    self.assertRaises(PreconditionError, hs110.receive, 123)
    self.assertRaises(PreconditionError, hs110.receive, 1.1)
    self.assertRaises(PreconditionError, hs110.receive, 3j)
    self.assertRaises(ValueError, hs110.receive, sample_data_fail)
    hs110.receive(sample_data_ok)
    hs110.receive(sample_data_h2)

  @given(text())
  @example('h1')
  @example('h2')
  def test_constructor(self, hardware):

    if (hardware in ['h1', 'h2']):
      empty_print = {
        'h1': 'current=0, voltage=0, power=0, total=0, err_code=0',
        'h2': 'current_ma=0, voltage_mv=0, power_mw=0, total_wh=0, err_code=0'
      }
      empty_value = {
        'h1': {
          "emeter": {
            "get_realtime": {
              "current": 0,
              "voltage": 0,
              "power": 0,
              "total": 0,
              "err_code": 0
            }
          }
        },
        'h2': {
          "emeter": {
            "get_realtime": {
              "current_ma": 0,
              "voltage_mv": 0,
              "power_mw": 0,
              "total_wh": 0,
              "err_code": 0
            }
          }
        }
      }

      hs110 = HS110data(hardware)
      self.assertEqual(hs110._HS110data__hardware, hardware)
      self.assertEqual(hs110._HS110data__received_data, empty_value[hardware])
      self.assertEqual(str(hs110), empty_print[hardware])

      self.assertEqual(hs110._HS110data__hardware, hardware)
      hs110._HS110data__received_data['emeter']['get_realtime'][hs110._HS110data__keyname[hardware]['current']] = 1
      hs110._HS110data__received_data['emeter']['get_realtime'][hs110._HS110data__keyname[hardware]['voltage']] = 220
      hs110._HS110data__received_data['emeter']['get_realtime'][hs110._HS110data__keyname[hardware]['power']] = 220
      hs110._HS110data__received_data['emeter']['get_realtime'][hs110._HS110data__keyname[hardware]['total']] = 1.3
      hs110._HS110data__received_data['emeter']['get_realtime']['err_code'] = 1

      hs110.reset_data()
      self.assertEqual(hs110._HS110data__received_data, empty_value[hardware])

    else:

      self.assertRaises(PreconditionError, HS110data, hardware)

  @given(integers(min_value=-100, max_value=70000))
  @example(9999)
  def test_port(self, port_number):
    if (port_number <0 or port_number >65535):
      self.assertRaises(PreconditionError, HS110data, port=port_number)
    else:
      hs110 = HS110data(port=port_number)
      self.assertEqual(hs110._HS110data__port, port_number)
  
  def test_get_cmd(self):
    cmd_encrypted = b'\x00\x00\x00\x1e\xd0\xf2\x97\xfa\x9f\xeb\x8e\xfc\xde\xe4\x9f\xbd\xda\xbf\xcb\x94\xe6\x83\xe2\x8e\xfa\x93\xfe\x9b\xb9\x83\xf8\x85\xf8\x85'
    hs110 = HS110data()

    self.assertEqual(hs110.get_cmd(), cmd_encrypted)

  @given(
    integers(min_value=1, max_value=255),    # IPv4 1st group
    integers(min_value=1, max_value=255),    # IPv4 2nd group
    integers(min_value=1, max_value=255),    # IPv4 3rd group
    integers(min_value=1, max_value=255),    # IPv4 4th group
    integers(min_value=0, max_value=65535))  # HS110 Port
  @example(192, 168, 1, 99, 9998)
  def test_get_connection_info(self, ip1, ip2, ip3, ip4, test_port):
    test_ip   = '%s.%s.%s.%s' % (ip1, ip2, ip3, ip4)
    info  =  "HS110 connection: %s:%s" % (test_ip, test_port)
    hs110 = HS110data(ip = test_ip, port = test_port)

    self.assertEqual(hs110.get_connection_info(), info)

  @patch.object(HS110data,'send')
  def test_connect(self, mock_HS110data_send):
    assert HS110data.send is mock_HS110data_send
    hs110 = HS110data()
    hs110.send('mycommand')
    mock_HS110data_send.assert_called_with('mycommand')

  @patch.object(socket.socket,'settimeout')
  @patch.object(socket.socket,'connect')
  @patch.object(socket.socket,'send')
  @patch.object(socket.socket,'recv')
  @patch.object(socket.socket,'close')
  @patch.object(socket.socket,'__init__')
  def test_socket(self, mock_init, mock_close, mock_recv, mock_send, mock_connect, mock_settimeout):
    assert socket.socket.settimeout is mock_settimeout
    assert socket.socket.connect is mock_connect
    assert socket.socket.send is mock_send
    assert socket.socket.recv is mock_recv
    assert socket.socket.close is mock_close
    assert socket.socket.__init__ is mock_init
    mock_init.return_value = None

    test_ip   = '192.168.1.100'
    test_port = 9991

    # Init hs110 object and return data
    hs110 = HS110data(ip = test_ip, port = test_port)
    sample_data = hs110._HS110data__encrypt('{"emeter":{"get_realtime":{"voltage_mv":229865,"current_ma":1110,"power_mw":231866,"total_wh":228,"err_code":0}}}')
    sample_data_dict = {'emeter': {'get_realtime': {'voltage_mv': 229865, 'current_ma': 1110, 'power_mw': 231866, 'total_wh': 228, 'err_code': 0}}}
    mock_recv.return_value = sample_data


    # Make connection and test called metheods
    hs110.connect()
    mock_init.assert_called_once()
    mock_settimeout.assert_called_once_with(2)
    mock_connect.assert_called_once_with((test_ip, test_port))
    mock_send.assert_called_once_with(hs110.get_cmd())
    mock_close.assert_called_once()
    self.assertEqual(hs110._HS110data__received_data, sample_data_dict)

    # Test socket exception from send
    mock_recv.side_effect = ValueError()
    with patch('builtins.print') as mock_print:
      hs110.send('mycommand')

      self.assertEqual(hs110._HS110data__received_data, hs110._HS110data__empty_data())
      assert mock_print.mock_calls == [
        call('[warning] Could not decrypt data from hs110. Reseting values.')
      ]

    mock_connect.side_effect = socket.error()
    with patch('builtins.print') as mock_print:
      hs110.send('mycommand')
      assert mock_print.mock_calls == [
        call('[error] Could not connect to the host 192.168.1.100:9991 Keeping last values')
      ]

  @patch('time.sleep')
  @patch.object(HS110data, 'connect')
  @patch('hs110exporter.start_http_server')
  def test_main(self, mock_http_server, mock_connect, mock_sleep):
    assert time.sleep is mock_sleep
    assert HS110data.connect is mock_connect
    mock_sleep.side_effect = Exception("Ignore it... just connect mock")

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--target", metavar="<ip>", required=False, help="Target IP Address", default="192.168.1.1", type=str)
    parser.add_argument("-f", "--frequency", metavar="<seconds>", required=False, help="Interval in seconds between checking measures", default=1, type=int)
    parser.add_argument("-p", "--port", metavar="<port>", required=False, help="Port for listenin", default=8110, type=int)
    args = parser.parse_args()

    with patch('builtins.print') as mock_print:
      assert mock_print is mock_print
      self.assertRaises(Exception, main, args)

      assert mock_print.mock_calls == [
        call("[info] HS110 connection: 192.168.1.1:9999"),
        call("[info] Exporter listenting on TCP: 8110"),
        call("[info] current_ma=0, voltage_mv=0, power_mw=0, total_wh=0, err_code=0")
      ]

    mock_connect.assert_called_once()
    assert mock_http_server.mock_calls == [ call(args.port) ]
    assert mock_sleep.mock_calls == [ call(args.frequency) ]

    fake_args = args
    fake_args.target = None
    self.assertRaises(PreconditionError, main, fake_args)

    fake_args = args
    fake_args.frequency = None
    self.assertRaises(PreconditionError, main, fake_args)

    fake_args = args
    fake_args.port = None
    self.assertRaises(PreconditionError, main, fake_args)

if __name__ == '__main__':
    unittest.main()