import socket
import types
import unittest
from StringIO import StringIO

from benderjab.util import get_config

class TestGetConfig(unittest.TestCase):
  def testDefault(self):
    cfg = StringIO("""[default]
jid: name@server.tld
password: badpassword
""")
    d = get_config(None, cfg)
    self.failUnless( hasattr(d, '__getitem__') )
    self.failUnless(d['jid'] == 'name@server.tld')
    self.failUnless(d['password'] == 'badpassword')

  def testHostname(self):
    hostname = socket.gethostname()
    cfg = StringIO("""[default]
jid: name@server.tld
password: badpassword

[%s]
password: otherbadpassword
""" % (hostname))
    d = get_config(None, cfg)
    self.failUnless( hasattr(d, '__getitem__') )
    self.failUnless(d['jid'] == 'name@server.tld')
    self.failUnless(d['password'] == 'otherbadpassword')

  def testCatchDefault(self):
    hostname = socket.gethostname()
    cfg = StringIO("""[default]
jid: romeo@montague.net
password: juliet
""")
    d = get_config(None, cfg)
    self.failUnless( d is None )

def suite():
  return unittest.makeSuite(TestGetConfig)

if __name__ == "__main__":
  unittest.main(defaultTest="suite")

