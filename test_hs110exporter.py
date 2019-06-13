#!/usr/bin/env python3
import unittest
import socket

from hs110exporter import validIP, encrypt, decrypt

class TestValidIP(unittest.TestCase):
  def test_ipstring(self):
    self.assertEqual(validIP('192.168.0.1'),'192.168.0.1')
    self.assertEqual(validIP(' 192.168.0.1 '),'192.168.0.1')

  def test_ipvalues(self):
    self.assertRaises(TypeError, validIP, 192)
    self.assertRaises(TypeError, validIP, 192.168)
    self.assertRaises(TypeError, validIP, 3j)
    self.assertRaises(ValueError, validIP, '192.168.0.1.a')

  def test_encryptstring(self):
    text_encrypted = b'\x00\x00\x00\x10\xd0\xf0\x98\xfd\x91\xfd\x92\xa8\x88\xff\x90\xe2\x8e\xea\xca\xb7'
    text_decrypted = '{ hello: world }'
    self.assertEqual(encrypt(text_decrypted), text_encrypted)
    self.assertEqual(decrypt(text_encrypted), text_decrypted)

  def test_encryptvalues(self):
    self.assertRaises(TypeError, encrypt, 100)
    self.assertRaises(TypeError, encrypt, 100.1)
    self.assertRaises(TypeError, encrypt, 3j)
    self.assertRaises(TypeError, encrypt, b'\x00\x00\x00\x10')
    self.assertIsInstance(encrypt('Hello world'), bytes)

  def test_decryptvalues(self):
    self.assertRaises(TypeError, decrypt, 100)
    self.assertRaises(TypeError, decrypt, 100.1)
    self.assertRaises(TypeError, decrypt, 3j)
    self.assertRaises(TypeError, decrypt, "Hello world")
    self.assertIsInstance(decrypt(b'\x00\x00\x00\x10'), str)

if __name__ == '__main__':
    unittest.main()