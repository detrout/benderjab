import socket
import types
import unittest
from StringIO import StringIO

from benderjab import bot
from benderjab import util
import xmlrpclib

import xmpp

class FakeClient:
    def send(self, msg):
        self.msg = msg

class TestBot(unittest.TestCase):
    def test_getter_setters(self):
        """
        Somewhat unnecessary testing of get/set
        """
        b = bot.BenderJab()
        t = "test@example.fake"
        b.jid = t
        self.failUnlessEqual(b.jid, t)
        
        self.failUnlessEqual(b.resource, 'BenderJab')
        r = 'resource'
        b.resource = 'resource'
        self.failUnlessEqual(b.resource, r)
        
    def test_filename_macro(self):
        """
        Make sure the log & pid file macro expansion works right
        """
        b = bot.BenderJab()
        b.jid = "test@example.fake"
        self.failUnlessEqual("/tmp/test@example.fake.BenderJab.pid", b.pid_filename)
        self.failUnlessEqual("/tmp/test@example.fake.BenderJab.log", b.log_filename)
        
        b.cfg['pid'] = "/tmp/foo.pid"
        self.failUnlessEqual("/tmp/foo.pid", b.pid_filename)
        
        b.cfg['log'] = "/tmp/%(password)s.log"
        self.failUnlessRaises(KeyError, b._get_log_filename)

    def test_authorized_user_parsing(self):
        """
        test the base authorized user code
        """
        b = bot.BenderJab()
        user1 = util.toJID('user1@example.fake')
        user2 = util.toJID('user1@example.fake')
        baduser =  util.toJID('evilhacker@empire.us')
        # by default authorize everything
        self.failUnlessEqual(b.check_authorization(user1), True)
        self.failUnlessEqual(b.check_authorization(user2), True)
        self.failUnlessEqual(b.check_authorization(baduser), True)
        
        # empty list is deny everyone
        b.authorized_users = []
        self.failUnlessEqual(b.check_authorization(user1), False)
        self.failUnlessEqual(b.check_authorization(user2), False)
        self.failUnlessEqual(b.check_authorization(baduser), False)
        
        # now make sure 
        user_list = "user1@example.fake other@fake.example"
        b.authorized_users = b._parse_user_list(user_list)
        self.failUnlessEqual(b.check_authorization(user1), True)
        self.failUnlessEqual(b.check_authorization(user2), True)
        self.failUnlessEqual(b.check_authorization(baduser), False)
        
    def test_authorized_message(self):
        b = bot.BenderJab()
        user_list = "user1@example.fake other@fake.example"
        b.authorized_users = b._parse_user_list(user_list)
        b.cl = FakeClient()
        
        fromjid = util.toJID('user1@example.fake')
        tojid = util.toJID('random_user@example.fake')
        body = u"test message"
        msg=xmpp.protocol.Message(tojid,body=body,typ='chat', frm=fromjid)
        b.messageCB(b.cl, msg)
        response = b.cl.msg.getBody()
        valid = 'I have no idea what "test message" means.'
        self.failUnlessEqual(valid, response)
        
        fromjid = util.toJID('eviluser@example.fake')
        msg=xmpp.protocol.Message(tojid,body=body,typ='chat', frm=fromjid)
        b.messageCB(b.cl, msg)
        response = b.cl.msg.getBody()
        self.failUnlessEqual('Authorization Error.', response)
        
    def test_check_jid_resource(self):
        """
        Make sure that we get a JIDMissingResource if required
        """
        b = bot.BenderJab()
        users_good = "user1@example.fake/resource user2@example.fake/resource"
        users_bad = "user1@example.fake/resource user2@example.fake"
        
        user_list1 = b._parse_user_list(users_good, require_resource=True)
        self.failUnlessRaises(bot.JIDMissingResource, 
                            b._parse_user_list,
                            users_bad,
                            require_resource=True)
  
def suite():
    return unittest.makeSuite(TestBot)

if __name__ == "__main__":
  unittest.main(defaultTest="suite")

