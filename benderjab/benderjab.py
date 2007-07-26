#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import commands
from getpass import getpass
from optparse import OptionParser
import re
import sys
import time
import types

import xmpp
from .util import toJID, get_password, get_config
 
class BenderJab(object):
  """Base class for a simple jabber bot

  self.eventTasks - list of things to do after an event timeout
  """
  def __init__(self, jid, password=None, resource=None):
    """Initialize our core jabber options, prompting for password if needed
    """
    if jid is None:
      jid = raw_input("jabber id: ")
    password = get_password(jid, password)
    if resource is None:
      resource = "BenderJab"

    self.jid = toJID(jid)
    self.resource = resource
    self.password = password
    # number of seconds to wait in each poll step
    self.timeout = 1
    self.parser = self._parser
    self.eventTasks = []

  def messageCB(self, conn, msg):
    """Simple handling of messages
    """
    who = msg.getFrom()
    body = msg.getBody()
     
    if body is None:
      return
    try:
      reply = self.parser(body, who)
    except Exception, e:
      reply = "failed: " + str(e)
      print e

    conn.send(xmpp.Message(to=who, typ='chat', body=reply))

  def _parser(self, message, who):
    """Default parser function, 
    overide this or replace self.parser with a different function
    to do something more useful
    """
    # some default commands
    if re.match("help", message):
      reply = "I'm sooo not helpful"
    elif re.match("time", message):
      reply = "Server time is "+time.asctime()
    elif re.match("uptime", message):
      reply = commands.getoutput("uptime")
    else:
      reply = "I have no idea what \""+message+"\" means."
    return reply

  def presenceCB(self, conn, msg):
    presence_type = msg.getType()
    who = msg.getFrom()
    # This code provides for a fairly promiscous bot
    # a more secure bot should check an auth list and accept deny
    # based on the incoming who JID
    if presence_type == "subscribe":
      # Tell the server that we accept their subscription request
      conn.send(xmpp.Presence(to=who, typ='subscribed'))
      # Ask to be their contact too
      conn.send(xmpp.Presence(to=who, typ='subscribe'))
      # Be friendly
      conn.send(xmpp.Message(who, "hi " + who.getNode()))
    elif presence_type == "unsubscribe":
      conn.send(xmpp.Message(who, "bye " + who.getNode()))
      conn.send(xmpp.Presence(to=who, typ='unsubscribed'))
      conn.send(xmpp.Presence(to=who, typ='unsubscribe'))

  def logon(self):
    """connect to server"""
    self.cl = xmpp.Client(self.jid.getDomain(), debug=[])
    # if you have dnspython installed and use_srv is True
    # the dns service discovery lookup seems to fail.
    self.cl.connect(use_srv=False)

    auth_state = self.cl.auth(self.jid.getNode(), self.password, self.resource)
    if auth_state is None:
      # auth failed
      print "couldn't authenticate", unicode(self.jid)
      # probably want a better exception here
      raise RuntimeError(self.cl.lastErr)

    # tell the xmpp client that we're ready to handle things
    self.cl.RegisterHandler('message', self.messageCB)
    self.cl.RegisterHandler('presence', self.presenceCB)

    # announce our existence to the server
    self.cl.sendInitPresence()
    # not needed but lets me muck around with the client from interpreter
    return self.cl

  def eventStep(self, conn):
    """single step through the event loop"""
    try:
      conn.Process(self.timeout)
      for f in self.eventTasks:
        f(self)
      return 1
    except KeyboardInterrupt:
      return 0

  def eventLoop(self, timeout=None):
    """Loop forever (or until timeout)
    """
    if timeout is None:
      while self.eventStep(self.cl):
        pass
    else:
      tstart = time.time()
      while self.eventStep(self.cl) and timeout > 0:
        tnow = time.time()
        timeout -= (tnow - tstart)
        tstart = tnow
    return

  def disconnect(self):
    self.cl.disconnect()

def BenderFactory(profile, filename='~/.benderjab'):
  """Use the config parser to get our login credentials
  """
  jidparams = get_config(profile)
  return BenderJab(**jidparams)

def makeOptions():
  parser = OptionParser()

  parser.add_option('-j', '--jid', dest="jid",
                    help="the jabber id we should connect as")
  return parser

def main(argv=None):
  if argv is None:
    argv = sys.argv
  arg_parser = makeOptions()
  opt, args = arg_parser.parse_args(argv)
 
  bot = BenderJab(opt.jid)
  bot.logon()
  bot.eventLoop()

if __name__ == "__main__":
  main()
