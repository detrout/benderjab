#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import sys,os,xmpp
from .util import get_config

def send(tojid, text, profile=None):
  """Quickly send a jabber message tojid

  :Parameters:
    - `tojid`: The Jabber ID to send to
    - `text`: a string containing the message to send
    - `profile`: which set of credentials to use from the config file
  """
  jidparams = get_config(profile)
  # if we have no credentials, don't bother logging in
  if jidparams is None:
    return

  jid=xmpp.protocol.JID(jidparams['jid'])
  # construct a client instance, logging into the JIDs servername
  # xmpp's default debug didn't work when I started using it
  cl=xmpp.Client(jid.getDomain(),debug=[])

  # if use_srv is true, xmpp will try to use dnspython to look up
  # the right server via a DNS SRV request, this doesn't work right
  # for my server
  cl.connect(use_srv=False)

  # try logging in
  if cl.auth(jid.getNode(),jidparams['password'], 'xsend') is None:
    print "Couldn't auth", cl.lastErr
  else:
    # we logged in, so we can send a message
    cl.send(xmpp.protocol.Message(tojid,text))

  # hang up politely
  cl.disconnect()

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
