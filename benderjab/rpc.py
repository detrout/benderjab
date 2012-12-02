"""
Provide support for XML-RPC over Jabber (JEP-0009)

The simplest way to use this is xmlrpc_call which packs up some arguments, sends
them to your receiving xml-rpc server, and waits for the response.

Alternatively one can have an event loop to wait for returning xml-rpc
messages sent with xmlrc_send. For that xmlrpc_extract_iq will unpack
the jabber message and return the xml-rpc (args, methodname) tuple
"""
import logging
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
import sys

import xmpp
from xmpp import simplexml

from benderjab.bot import BenderJab
from benderjab.util import toJID
from benderjab.xsend import connect

class XmlRpcReceiveTimeout(IOError):
    """
    We timed out waiting for an xml-rpc message to come back
    """

class XmlRpcProtocolError(IOError):
    """
    There was a problem extracting the parameters out of the jabber message
    """

def make_iq(tojid, typ, marshaled, msgid=None):
    """
    Wrap XML-RPC marshaled data in an XMPP jabber:iq:rpc message
    """
    tojid = toJID(tojid)
    iq = xmpp.Iq(typ=typ, to=tojid, xmlns=None)
    if msgid is not None:
      iq.setID(msgid)
    query = iq.addChild('query', namespace=xmpp.NS_RPC)
    query.addChild(node=simplexml.XML2Node(marshaled))
    return iq

def extract_iq(iq):
    """
    Extract xml-rpc xml from a jabber:iq:rpc message

    You'll need to run the return value through either
      loads
      dispatch_message

    returns None if there wasn't a body to extract
    """
    children = iq.getChildren()
    if len(children) < 1:
        errmsg = u"Iq didn't have a body to extract"
        logging.debug(errmsg + u": " + unicode(iq))
        raise XmlRpcProtocolError(errmsg)
    elif len(children) > 1:
        errmsg = u"Too many child nodes"
        logging.debug(errmsg + u": " + unicode(iq))
        raise XmlRpcProtocolError(errmsg)
    else:
        return str(children[0])

def error_iq(who, err_attrs, description, body, msgid=None):
    iq = xmpp.Iq(typ='error', to=who)
    if msgid is not None:
        iq.setID(msgid)
    iq.addChild(node=simplexml.XML2Node(str(body)))
    error = iq.addChild('error', err_attrs)
    error.addChild(description, namespace='urn:ietf:params:xml:ns:xmpp-stanzas')
    return iq

def send(conn, tojid, params, methodname=None, encoding=None):
    """
    Send an xml-rpc message via jabber

    JEP-009 http://www.xmpp.org/extensions/xep-0009.html
    """
    call_xml = xmlrpclib.dumps(params, methodname, encoding)

    iq = make_iq(tojid, 'set', call_xml)
    msg_id = conn.send(iq)
    return msg_id

def receive(conn, msgid, timeout=25):
    """
    Wait on conn for an xmlrpc return call

    :Throw:
      `XmlRpcReceiveTimeout` - the WaitForResponse timed out
      `xmlrpclib.Fault` - there was an error with the remote function call
    """
    msg = conn.WaitForResponse(msgid, timeout)
    if msg is None:
        raise XmlRpcReceiveTimeout("message %s timed out" %(str(id)))

    body = extract_iq(msg)
    return xmlrpclib.loads(body)

def call(conn, tojid, params, methodname=None, encoding=None):
    msgid = send(conn,tojid, params, methodname, encoding)
    reply_iq = receive(conn, msgid)
    return reply_iq[0]


class XmlRpcBot(BenderJab, SimpleXMLRPCDispatcher):
    def __init__(self, section=None, configfile=None):
        super(XmlRpcBot, self).__init__(section, configfile)
        self.cfg['authorized_users'] = None

        allow_none = False
        encoding = None
        # SimpleXMLRPCDispatcher is still an "old-style" class,
        # so super doesn't work right
        #
        # further ick, this is an 'internal' class so signature changed
        # between python2.4 and python2.5
        if sys.version_info[0] == 2 and sys.version_info[1] > 4:
            # python 2.5 version
            SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)
        else:
            # python 2.3, 2.4 version
            SimpleXMLRPCDispatcher.__init__(self)
        self.authorized_users = None

    def read_config(self, section=None, configfile=None):
        super(XmlRpcBot, self).read_config(section, configfile)

    def logon(self):
        """
        """
        cl = BenderJab.logon(self)
        cl.RegisterHandler('iq', self.bot_dispatcher, typ='set', ns=xmpp.NS_RPC)

    def rpc_send(self, tojid, args, method):
        """
        Send a XMl-RPC message to tojid.
        """
        if self.cl is None:
            msg = "Bot isn't connected to the server"
            logging.fatal(msg)
            raise RuntimeError(msg)
        msg = 'RPC Send <%s>: %s' %(str(tojid),str(method) + str(args))
        logging.debug(msg)
        return send(self.cl, tojid, args, method)

    def rpc_call(self, tojid, args, method):
        """
        Send a XML-RPC message to tojid, and return the response
        """
        if self.cl is None:
            msg = "Bot isn't connected to the server"
            logging.fatal(msg)
            raise RuntimeError(msg)
        msg = 'RPC Call <%s>: %s' %(str(tojid), str(method) + str(args))
        logging.debug(msg)
        result = call(self.cl, tojid, args, method)
        logging.debug("Result: " + str(result))
        return result

    def bot_dispatcher(self, conn, msg):
        msgid =None

        try:
            who = msg.getFrom()
            msgid = msg.getID()
            body = extract_iq(msg)
            if not (self.authorized_users is None or self.check_authorization(who)):
                err_attrs = {'code': 503, 'type': 'auth'}
                response_iq = error_iq(who, err_attrs, 'forbidden', body, msgid)
            else:
                response = self._marshaled_dispatch(body)
                response_iq = make_iq(who, 'result', response, msgid)
            c = conn.send(response_iq)
        except RuntimeError,e:
            self.log.error("Exception in bot_dispatcher"+str(e))
            # really should send an error back to the sender
        raise xmpp.NodeProcessed
