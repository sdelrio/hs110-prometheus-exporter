#!/usr/bin/env python3
import unittest
import socket

from hs110exporter import validIP, HS110data

class TestValidIP(unittest.TestCase):
  def test_ipstring(self):
    self.assertEqual(validIP('192.168.0.1'),'192.168.0.1')
    self.assertEqual(validIP(' 192.168.0.1 '),'192.168.0.1')

  def test_ipvalues(self):
    self.assertRaises(TypeError, validIP, 192)
    self.assertRaises(TypeError, validIP, 192.168)
    self.assertRaises(TypeError, validIP, 3j)
    self.assertRaises(ValueError, validIP, '192.168.0.1.a')

class TestHS110data(unittest.TestCase):
  def test_encryptstring(self):
    hs110 = HS110data()
    text_encrypted = b'\x00\x00\x00\x10\xd0\xf0\x98\xfd\x91\xfd\x92\xa8\x88\xff\x90\xe2\x8e\xea\xca\xb7'
    text_decrypted = '{ hello: world }'

    self.assertEqual(hs110._HS110data__encrypt(text_decrypted), text_encrypted)
    self.assertEqual(hs110._HS110data__decrypt(text_encrypted), text_decrypted)


  def test_encryptvalues(self):
    hs110 = HS110data()

    self.assertRaises(TypeError, hs110._HS110data__encrypt, 100)
    self.assertRaises(TypeError, hs110._HS110data__encrypt, 100.1)
    self.assertRaises(TypeError, hs110._HS110data__encrypt, 3j)
    self.assertRaises(TypeError, hs110._HS110data__encrypt, b'\x00\x00\x00\x10')
    self.assertIsInstance(hs110._HS110data__encrypt('Hello world'), bytes)

  def test_decryptvalues(self):
    hs110 = HS110data()

    self.assertRaises(TypeError, hs110._HS110data__decrypt, 100)
    self.assertRaises(TypeError, hs110._HS110data__decrypt, 100.1)
    self.assertRaises(TypeError, hs110._HS110data__decrypt, 3j)
    self.assertRaises(TypeError, hs110._HS110data__decrypt, "Hello world")
    self.assertIsInstance(hs110._HS110data__decrypt(b'\x00\x00\x00\x10'), str)

  def test_received_data(self):
    hs110 = HS110data()

    self.assertRaises(TypeError, hs110.get_data, 100)
    self.assertRaises(TypeError, hs110.get_data, 100.1)
    self.assertRaises(TypeError, hs110.get_data, 3j)
    self.assertRaises(ValueError, hs110.get_data, "nonexist")

  def test_constructor(self):
    self.assertRaises(ValueError, HS110data, hardware_version='h999')
    hs110 = HS110data('h1')
    self.assertEqual(hs110._HS110data__hardware, 'h1')
    hs110 = HS110data('h2')
    self.assertEqual(hs110._HS110data__hardware, 'h2')
    hs110 = HS110data()
    self.assertEqual(hs110._HS110data__hardware, 'h2')

if __name__ == '__main__':
    unittest.main()