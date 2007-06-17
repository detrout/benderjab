#!/usr/bin/env python

import commands
from getpass import getpass
from optparse import OptionParser
import re
import sys
import time
import types

import xmpp

def toJID(jid):
  """cast strings to a jabberid"""
  if type(jid) in types.StringTypes:
    return xmpp.protocol.JID(jid)
  else: 
    return jid
 
class BenderJab(object):
  """Base class for a simple jabber bot

  self.parser = "an alternate command parser to use"
  self.eventTasks = "list of things to do after an event timeout"
  """
  def __init__(self, jid, password=None, resource=None):
    """Initialize our core jabber options, prompting for password if needed
    """
    if jid is None:
      jid = raw_input("jabber id: ")
    if password is None:
      password = getpass("enter password: ")
    if resource is None:
      resource = "BenderJab"

    self.jid = toJID(jid)
    self.resource = resource
    self.password = password

    self.parser = None
    self.eventTasks = []
  def messageCB(self, conn, msg):
    """Simple handling of messages
    """
    print u"DEBUG:", unicode(msg)
    who = msg.getFrom()
    print u"Sender:", unicode(who)

    body = msg.getBody()
    print u"Content:", unicode(body)

     
    if body is None:
      return
    try:
      if self.parser is not None:
        reply = self.parser(body)
      else:
        # some default commands
        if re.match("help", body):
          reply = "I'm sooo not helpful"
        elif re.match("time", body):
          reply = "Server time is "+time.asctime()
        elif re.match("uptime", body):
          reply = commands.getoutput("uptime")
        else:
          reply = "I have no idea what \""+body+"\" means."
    except Exception, e:
      reply = "failed: " + str(e)

    conn.send(xmpp.Message(to=who, typ='chat', body=reply))

  def presenceCB(self, conn, msg):
    print "from pres:", msg.getFrom(), msg.getStatus()
    presence_type = msg.getType()
    who = msg.getFrom()
    if presence_type == "subscribe":
      conn.send(xmpp.Presence(to=who, typ='subscribed'))
      conn.send(xmpp.Presence(to=who, typ='subscribe'))
      conn.send(xmpp.Message(who, "hi " + who.getNode()))
    elif presence_type == "unsubscribe":
      conn.send(xmpp.Message(who, "bye " + who.getNode()))
      conn.send(xmpp.Presence(to=who, typ='unsubscribed'))
      conn.send(xmpp.Presence(to=who, typ='unsubscribe'))

  def logon(self):
    """connect to server"""
    self.cl = xmpp.Client(self.jid.getDomain(), debug=[])
    self.cl.connect(use_srv=False)

    auth_state = self.cl.auth(self.jid.getNode(), self.password, self.resource)
    if auth_state is None:
      # auth failed
      print "couldn't authenticate", unicode(self.jid)
      # probably want a better exception here
      raise RuntimeError(self.cl.lastErr)

    # we want to do stuff 
    self.cl.RegisterHandler('message', self.messageCB)
    self.cl.RegisterHandler('presence', self.presenceCB)

    self.cl.sendInitPresence()
    return self.cl

  def eventStep(self, conn):
    """single step through the event loop"""
    try:
      conn.Process(1)
      for f in self.eventTasks:
        f()
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
