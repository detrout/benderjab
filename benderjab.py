#!/usr/bin/env python

from getpass import getpass
import time
import types

import xmpp

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

class BenderJab(object):
  """Base class for a simple jabber bot
  """
  def __init__(self, jid, password=None, resource=None):
    """Initialize our core jabber options, prompting for password if needed
    """
    if password is None:
      password = getpass("enter password: ")
    if resource is None:
      resource = "BenderJab"

    self.jid = toJID(jid)
    self.resource = resource
    self.password = password

  def messageCB(self, conn, msg):
    """Simple handling of messages
    """
    print "DEBUG:", str(msg)
    who = msg.getFrom()
    print "Sender:", str(who)

    body = msg.getBody()
    print "Content:", str(body)

     
    if body is None:
      return
    if body[:4] == "help":
      conn.send(xmpp.Message(to=who, typ='chat', body="no help here"))
    if body[:4] == "time":
      conn.send(xmpp.Message(to=who, typ='chat',body=time.asctime() ))

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
      print "couldn't authenticate", str(jid)
      # probably want a better exception here
      raise RuntimeError(self.cl.lastErr)

    # we want to do stuff 
    self.cl.RegisterHandler('message', self.messageCB)
    self.cl.RegisterHandler('presence', self.presenceCB)

    self.cl.sendInitPresence()
    return self.cl
 
  def eventLoop(self, timeout=None):
    """Loop forever (or until timeout)
    """
    if timeout is None:
      while StepOn(self.cl):
        pass
    else:
      while StepOn(self.cl) and timeout > 0:
        timeout -= 1
    return

  def disconnect(self):
    self.cl.disconnect()

def main():
  jid = "jumpgate@chaos.caltech.edu"
  bot = BenderJab(jid)
  bot.logon()
  bot.eventLoop()

if __name__ == "__main__":
  main()
