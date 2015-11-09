#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import ConfigParser
from getpass import getpass
import os
import socket
import types

import xmpp

def toJID(jid):
  """
  Make sure we have a JabberID object

  If it is already a jabberID don't do anything

  :Parameters:
    - `jid`: something that looks like a jabber id
  """
  if type(jid) in types.StringTypes:
    return xmpp.protocol.JID(jid)
  else:
    return jid

def get_checked_password(jid, password=None):
  """
  Prompt for a password twice and make sure they match

  :Parameters:
    - `prompt`: the string to display to the user
  """
  prompt = u"Password for ["+ unicode(jid) +"]:"
  if password is None:
    ok = False
    while not ok:
      password = getpass(prompt)
      password2 = getpass(prompt)
      if password == password2:
        ok = True
      else:
        print("password mismatch, try again")
  return password

def get_password(jid, password=None):
  """
  Convience function to ask for a password with a nice prompt, if one is needed

  :Parameters:
    - `jid`: which jabber ID to ask for a password for
    - `password`: pass in a potential passsword, if its not none
                  we wont do anything.
  """
  if password is None:
    prompt = u"Password for ["+ unicode(jid) +"]:"
    password = getpass(prompt)
  return password

def get_config(profile=None, filename='~/.benderjab'):
  """Read config file, returning the specified section

  Also creates the file if it doesn't exist.

  :Parameters:
    - `profile`: which section of the config file to return
  """
  default={'jid':'romeo@montague.net','password':'juliet'}
  config = ConfigParser.RawConfigParser()

  if type(filename) in types.StringTypes:
    config_file = os.path.expanduser(filename)
    if not os.access(config_file,os.R_OK):
      # make a default file and exit
      config = ConfigParser.RawConfigParser(default)
      config.write(open(config_file,'w'))
      print("Please edit",filename,"to include a valid JID for sending messages")
      return None
    else:
      config.read(config_file)
  else:
    # (Well its not really a filename at this point)
    config.readfp(filename)

  # Grab stuff out of default
  params = {}
  if config.has_section('default'):
    params.update( dict(config.items('default')) )

  # then lets see if we have a hostname specific group
  if profile is None:
    hostname = socket.gethostname()
    if config.has_section(hostname):
      params.update( dict(config.items( socket.gethostname() )))
  else:
    if config.has_section(profile):
      params.update( dict(config.items(profile)) )

  if params == default:
    print("Please edit",filename,"to include a valid JID for sending messages")
    return None

  return params
