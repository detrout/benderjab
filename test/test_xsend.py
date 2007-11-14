import socket
import types
import unittest
from StringIO import StringIO

from benderjab import xsend
import xmlrpclib

class TestXSend(unittest.TestCase):
    def test_xmlrpc_pack_unpack(self):
        params = (1,2,['a','b'])
        marshaled = xmlrpclib.dumps(params)
        tojid = 'test@test.org'
        typ = 'set'
        iq = xsend.xmlrpc_make_iq(tojid, typ, marshaled, msgid=None)
        return_xml = xsend.xmlrpc_extract_iq(iq)
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
    #    iq = xsend.xmlrpc_make_iq(tojid, typ, marshaled, msgid=None)
    #    error = xsend.xmlrpc_error_iq(tojid, 500, 'error', iq)
    #    print error
    #     
    #    # def xmlrpc_error_iq(who, errcode, body, msgid=None):

def suite():
    return unittest.makeSuite(TestXSend)

if __name__ == "__main__":
  unittest.main(defaultTest="suite")

