#!/usr/bin/env python3
import unittest
import socket

from hs110exporter import validIP

class TestValidIP(unittest.TestCase):
  def test_ipstring(self):
    self.assertEqual(validIP('192.168.0.1'),'192.168.0.1')

  def test_ipvalues(self):
    self.assertRaises(TypeError, validIP, 192)
    self.assertRaises(TypeError, validIP, 192.168)
    self.assertRaises(TypeError, validIP, 3j)
    self.assertRaises(ValueError, validIP, '192.168.0.1.a')

if __name__ == '__main__':
    unittest.main()