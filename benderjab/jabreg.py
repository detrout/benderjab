#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
"""
This module handles implementing jabber in-band registration XEP-0077

http://www.xmpp.org/extensions/xep-0077.html
"""
from getpass import getpass
from optparse import OptionParser
import os
import sys
import types

import xmpp
from util import get_checked_password, get_password, toJID

def connect(jid):
  """Connect to jabber server for the specified JID
  """
  cl = xmpp.Client(jid.getDomain(), debug=[])
  cl.connect(use_srv=False)
  if cl.isConnected() is None:
    print(cl.lastErr)
    raise RuntimeError("Unable to connect to server" + jid.getDomain())
  return cl

def register(jid, email=None, password=None):
  """
  Register a new jabber ID
  """
  if email is None:
    email = str(jid)
  password = get_checked_password(jid, password)
  jid = toJID(jid)

  # connect to server
  cl = connect(jid)

  # ask the server to start the registration process
  # http://www.xmpp.org/extensions/xep-0077.html#usecases-register
  # <iq type='get' id='reg1'>  <query xmlns='jabber:iq:register'/> </iq>
  iq = xmpp.Iq(typ='get')
  iq.addChild('query', namespace=xmpp.NS_REGISTER)
  ready = cl.SendAndWaitForResponse(iq)

  # just check for an error response
  if ready.getErrorCode() is not None:
    raise RuntimeError(ready.getError())

  # send registration data (something like...)
  # <iq type='result' id='reg1'>
  #   <query xmlns='jabber:iq:register'>
  #    <registered/>
  #    <username>juliet</username>
  #    <password>R0m30</password>
  #    <email>juliet@capulet.com</email>
  #  </query>
  # </iq>
  iq = xmpp.Iq(typ='set')
  query = iq.addChild('query', namespace=xmpp.NS_REGISTER)
  query.addChild('username',payload=jid.getNode())
  query.addChild('password',payload=password)
  query.addChild('email',payload=email)
  register = cl.SendAndWaitForResponse(iq)
  if register.getErrorCode() is not None:
    raise RuntimeError(register.getError())

  return register

def unregister(jid, password=None):
  """Try to unregister a JID"""
  jid = toJID(jid)
  password = get_password(jid, password)

  cl = connect(jid)
  if cl.auth(jid.getNode(), password, "testing") is None:
    raise RuntimeError("Couldn't authenticate "+str(cl.lastErr))

  # XEP-0077 seems to suggest to should be user id
  # but the jabberd 1.4 faq says it should be the server name
  iq = xmpp.Iq(typ='set', to=jid.getDomain())
  query = iq.addChild('query', namespace=xmpp.NS_REGISTER)
  query.addChild('remove')
  response = cl.SendAndWaitForResponse(iq)
  if response.getErrorCode() is not None:
    raise RuntimeError(response.getError())

def test_logon(jid):
  prompt = "Password for ["+ jid +"]:"
  password = getpass(prompt)
  jid = toJID(jid)

  cl = connect(jid)

  if cl.auth(jid.getNode(), password, "testing") is None:
    print("Couldn't authenticate", cl.lastErr)

  cl.sendInitPresence()
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
    if opt.verbose: print("register", opt.register_jid)
    register(opt.register_jid, opt.email)
  if opt.unregister_jid is not None:
    if opt.verbose: print("unregister", opt.unregister_jid)
    unregister(opt.unregister_jid)
  if opt.test_jid is not None:
    if opt.verbose: print("test", opt.test_jid)
    test_logon(opt.test_jid)

  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
