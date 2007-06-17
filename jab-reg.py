#!/usr/bin/env python

from getpass import getpass
from optparse import OptionParser
import os
import sys
import signal
import time
import types

import xmpp

import mypw

def toJID(jid):
  """cast strings to a jabberid"""
  if type(jid) in types.StringTypes:
    return xmpp.protocol.JID(jid)
  else: 
    return jid
 
def StepOn(conn):
  """single step through the event loop"""
  try:
    conn.Process(1)
    return 1
  except KeyboardInterrupt:
    return 0

def GoOn(conn):
  """continue running the event loop"""
  while StepOn(conn):
    pass

def messageCB(conn, msg):
  print "Sender:", str(msg.getFrom())
  print "Content:", str(msg.getBody())
  print msg

def presenceCB(conn, msg):
  print "from:", msg.getFrom(), msg.getStatus()
  presence_type = msg.getType()
  who = msg.getFrom()
  if presence_type == "subscribe":
    conn.send(xmpp.Presence(to=who, typ='subscribed'))
    conn.send(xmpp.Presence(to=who, typ='subscribe'))

class registerIqCB:
  NS = 'jabber:iq:register'
  def __init__(self, username, password, email):
    self.username = username
    self.password = password
    self.email = email
    self.messages = []

    self.registered = False
    self.done = False

    self.error = None
    self.errorCode = None

  def sendRegistrationRequest(self, conn):
    # build our initial registration request
    iq = xmpp.Iq()
    iq.setType('get')
    iq.setQueryNS(self.NS)
    conn.send(iq)

  def sendRegistrationDetails(self, conn):
    iq = xmpp.Iq(typ="set",xmlns=None)
    iq.setQueryNS(self.NS)
    query = iq.getPayload()[0]
    query.addChild('username',payload=self.username)
    query.addChild('password',payload=self.password)
    query.addChild('email',payload=self.email)
    print "send", str(iq)
    conn.send(iq)
    print
    self.registered = True

  def getPayloadTag(msg, name):
    """recursively look through the message for the specified tag
    """
    for element in msg.getPayload():
      tag = element.getTags(name)
      if tags is not None:
        return tag
    return None

  def __call__(self, conn, msg):
    print "msg:", str(msg)
    self.messages.append(msg)
 
    if msg.getErrorCode() is not None:
      self.error = msg.getError()
      self.errorCode = msg.getErrorCode()
      self.done = True

    if not self.registered:
      self.sendRegistrationDetails(conn)

    if len(msg.getPayload()) == 0:
      self.done = True

def register(jid, email):
  if email is None:
    email = str(jid)
  prompt = "Password for ["+ jid +"]:"
  passwd = getpass(prompt)
  jid = toJID(jid)

  print "jid", jid, jid.getDomain()
  cl = xmpp.Client(jid.getDomain(), debug=[])
  cl.connect(use_srv=False)
  if cl.isConnected() is None:
    print "Unable to connect to server", jid.getDomain()
    print cl.lastErr
    return 1
  
  handler = registerIqCB(jid.getNode(), passwd, email)
  cl.RegisterHandler('iq', handler, ns=registerIqCB.NS)

  handler.sendRegistrationRequest(cl)

  while not handler.done:
    cl.Process(1)

  if handler.errorCode is not None:
    print "Error["+handler.errorCode+"]", handler.error
  
  cl.UnregisterHandler('iq', registerIqCB, ns=ns)
  return cl


def test_logon(jid):
  prompt = "Password for ["+ jid +"]:"
  passwd = getpass(prompt)
  jid = toJID(jid)

  cl = xmpp.Client(jid.getDomain(), debug=[])
  cl.connect(use_srv=False)

  if cl.auth(jid.getNode(), passwd, "testing") is None:
    print "Couldn't authenticate", cl.lastErr

  cl.RegisterHandler('message', messageCB)
  cl.RegisterHandler('presence', presenceCB)

  cl.sendInitPresence()
  for x in range(5):
    StepOn(cl)
  return cl

def makeOptionParser():
  parser = OptionParser()
  
  parser.set_defaults(verbose=False)
  parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                    help="report what I'm doing")

  parser.add_option('-r', '--register', dest='register_jid',
                     help="register a new jabber ID, prompting for a password")
  parser.add_option('-e', '--email', dest='email',
         help="set email address (for register)")

  parser.add_option('-u', '--unregister', dest='unregister_jid',
                     help="unregister a jabber ID")

  parser.add_option('-t', '--test', dest='test_jid',
         help="attempt to login with a jabber ID, prompting for password")

  return parser

def main(argv=None):
  if argv is None:
    argv = sys.argv[1:]

  parser = makeOptionParser()
  opt, arguments = parser.parse_args(argv)
  
  if opt.register_jid is not None:
    if opt.verbose: print "register", opt.register_jid
    register(opt.register_jid, opt.email)
  if opt.unregister_jid is not None:
    if opt.verbose: print "unregister", opt.unregister_jid
  if opt.test_jid is not None:
    if opt.verbose: print "test", opt.test_jid
    test_logon(opt.test_jid)

  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
