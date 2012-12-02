import socket
import types
import unittest
from StringIO import StringIO
import xmlrpclib

from benderjab import rpc
import xmpp

class fake_conn(object):
   def __init__(self):
     self.messages = []

   def send(self, msg):
     self.messages.append(msg)


class TestRPC(unittest.TestCase):
    def test_xmlrpc_pack_unpack(self):
        params = (1,2,['a','b'])
        marshaled = xmlrpclib.dumps(params)
        tojid = 'test@test.org'
        typ = 'set'
        iq = rpc.make_iq(tojid, typ, marshaled, msgid=None)
        return_xml = rpc.extract_iq(iq)
        unmarshaled = xmlrpclib.loads(return_xml)
        # loads returns (params, methodname)
        self.failUnlessEqual(unmarshaled[0], params)

    # FIXME: figure out xmlrpc_error_iq api
    #def test_xmlrpc_error(self):
    #    """
    #    Does the xmlrpc error code generate the right thing
    #    """
    #    params = (1,2,['a','b'])
    #    marshaled = xmlrpclib.dumps(params)
    #    tojid = 'test@test.org'
    #    typ = 'set'
    #    iq = rpc.make_iq(tojid, typ, marshaled, msgid=None)
    #    error = xsend.xmlrpc_error_iq(tojid, 500, 'error', iq)
    #    print error
    #
    #    # def error_iq(who, errcode, body, msgid=None):

    def test_xmlrpcbot(self):
       """
       Basic test of the XML-RPC class
       """
       bot = rpc.XmlRpcBot()
       def add(x, y):
         return x+y
       bot.register_function(add)
       params = xmlrpclib.dumps((1,2),'add')
       msg = rpc.make_iq('test@test.fake', 'set', params)
       conn = fake_conn()
       self.failUnlessRaises(xmpp.NodeProcessed, bot.bot_dispatcher, conn, msg)
       self.failUnless(len(conn.messages) == 1)
       result_xml = rpc.extract_iq(conn.messages[0])
       result_tuple = xmlrpclib.loads(result_xml)
       result = result_tuple[0][0]
       self.failUnlessEqual(3, result)


def suite():
    return unittest.makeSuite(TestRPC)

if __name__ == "__main__":
  unittest.main(defaultTest="suite")
