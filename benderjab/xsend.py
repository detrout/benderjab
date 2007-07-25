#!/usr/bin/env python
# $Id: xsend.py,v 1.1 2004/06/20 09:45:09 snakeru Exp $
import sys,os,xmpp
import ConfigParser


def send(tojid, text, profile='DEFAULT'):
  """Quickly send a jabber message tojid

  :Parameters:
    - `tojid`: The Jabber ID to send to
    - `text`: a string containing the message to send
    - `profile`: which set of credentials to use from the config file
  """
  jidparams = get_config(profile)
  if jidparams is None:
    return

  jid=xmpp.protocol.JID(jidparams['jid'])
  cl=xmpp.Client(jid.getDomain(),debug=[])

  cl.connect(use_srv=False)

  if not cl.auth(jid.getNode(),jidparams['password'], 'xsend'):
    print "Couldn't auth", cl.lastErr
  else:
    #cl.SendInitialPresence()
    cl.send(xmpp.protocol.Message(tojid,text))

  cl.disconnect()

def main(args=None):
  if args is None:
    args = sys.argv

  if len(args) < 2:
    print "Syntax: xsend JID text"
    return 1

  tojid=args[1]
  text=' '.join(args[2:])
  send(tojid, text)
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv))
