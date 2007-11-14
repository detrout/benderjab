#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import os
import random
import sys
import time
import xmlrpclib

import xmpp
from xmpp import simplexml

from util import get_config, toJID

def connect(profile=None):
  """
  Connect to the server for our jabber id
  """
  jidparams = get_config(profile)
  # if we have no credentials, don't bother logging in
  if jidparams is None:
    return

  myjid=toJID(jidparams['jid'])
  # construct a client instance, logging into the JIDs servername
  # xmpp's default debug didn't work when I started using it
  cl=xmpp.Client(myjid.getDomain(),debug=[])

  connection_type = ''
  connection_tries = 3

  # if use_srv is true, xmpp will try to use dnspython to look up
  # the right server via a DNS SRV request, this doesn't work right
  # for my server

  while connection_type == '' and connection_tries > 0:
    connection_type = cl.connect(use_srv=False)
    # wait a random length of time between 2.5 and 7.5 seconds
    # if we didn't manage to connect
    if connection_type == '':
      time.sleep( 5 + (random.random()*5 - 2.5))

  # connection failed
  if connection_type == '':
    raise IOError("unable to connect to" + str(cl.Server))
  
  # try logging in
  if cl.auth(myjid.getNode(),jidparams['password'], 'xsend') is None:
    raise IOError("Couldn't auth:"+str(cl.lastErr))
  
  return cl
  
def send(tojid, text, profile=None):
  """Quickly send a jabber message tojid
  
  :Parameters:
    - `tojid`: The Jabber ID to send to
    - `text`: a string containing the message to send
    - `profile`: which set of credentials to use from the config file
  """
  cl = connect(profile)
  # we logged in, so we can send a message
  cl.send(xmpp.protocol.Message(tojid,text))

  # hang up politely
  cl.disconnect()

def xmlrpc_make_iq(tojid, typ, marshaled, msgid=None):
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

def xmlrpc_send(conn, tojid, params, methodname=None, encoding=None):
    """
    Send an xml-rpc message via jabber 
    
    JEP-009 http://www.xmpp.org/extensions/xep-0009.html
    """    
    call_xml = xmlrpclib.dumps(params, methodname, encoding)
    
    iq = xmlrpc_make_iq(tojid, 'set', call_xml) 
    msg_id = conn.send(iq)
    return msg_id

def xmlrpc_extract_iq(iq):
    """
    Extract marshaled data from a jabber:iq:rpc message
    """
    children = iq.getChildren()
    if len(children) != 1:
      print "error!"
      print str(iq)
    return str(children[0])   


class XmlRpcReceiveTimeout(IOError):
    """
    We timed out waiting for an xml-rpc message to come back
    """
    
def xmlrpc_recv(conn, msgid, timeout=25):
    """
    Wait on conn for an xmlrpc return call
    
    :Throw:
      `XmlRpcReceiveTimeout` - the WaitForResponse timed out
      `xmlrpclib.Fault` - there was an error with the remote function call
    """
    msg = conn.WaitForResponse(msgid, timeout)
    if msg is None:
        raise XmlRpcReceiveTimeout("message %s timed out" %(str(id)))
  
    body = xmlrpc_extract_iq(msg)
    returnvalue = xmlrpclib.loads(body)
    return returnvalue

def xmlrpc_call(conn, tojid, params, methodname=None, encoding=None):
    msgid = xmlrpc_send(conn,tojid, params, methodname, encoding)
    reply_iq = xmlrpc_recv(conn, msgid)
    return reply_iq[0]
    
def xmlrpc_error_iq(who, err_attrs, description, body, msgid=None):
    iq = xmpp.Iq(typ='error', to=who)
    if msgid is not None:
      iq.setID(msgid)
    iq.addChild(node=simplexml.XML2Node(str(body)))
    error = iq.addChild('error', err_attrs)
    error.addChild(description, namespace='urn:ietf:params:xml:ns:xmpp-stanzas')
    return iq
    
def main(args=None):
    if args is None:
        args = sys.argv

    if len(args) < 2:
        print "Syntax: xsend JID text"
        return 1

    # parse command line arguments
    tojid=args[1]
    text=' '.join(args[2:])
    send(tojid, text)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
