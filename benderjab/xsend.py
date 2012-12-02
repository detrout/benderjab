#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import optparse
import os
import random
import sys
import time

import xmpp
from xmpp import simplexml

from benderjab.util import get_config, toJID

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

def wait_for_pid(pid, timeout=10):
    """
    Wait for a process id to disappear before returning

    pid is the process id to watch
    time out is how long in seconds to wait between polls
    """

    while True:
        try:
            os.kill(pid, 0)
        except OSError, e:
            # there is no PID, return
            return
        time.sleep(timeout)

def make_parser():
    usage = "%prog: [options] jabber-id message..."
    parser = optparse.OptionParser()

    parser.add_option('--wait-for-pid', type='int',
           help="Wait for a process ID to exit before sending message",
           default=None)

    return parser

def main(cmdline=None):
    parser = make_parser()
    opt, args = parser.parse_args(cmdline)

    if len(args) < 2:
        parser.error("Need JabberID and a message")

    if opt.wait_for_pid is not None:
        wait_for_pid(opt.wait_for_pid)

    # parse command line arguments
    tojid=args[1]
    message=' '.join(args[2:])

    send(tojid, message)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
