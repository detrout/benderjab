#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import ConfigParser
from getpass import getpass
import os
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
        print "password mismatch, try again"
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

def get_config(profile='DEFAULT', filename='~/.benderjab'):
  """Read config file, returning the specified section

  Also creates the file if it doesn't exist.

  :Parameters:
    - `profile`: which section of the config file to return
  """
  config_file = os.path.expanduser(filename)
  jidparams={'jid':'romeo@montague.net','password':'juliet'}
  config = ConfigParser.RawConfigParser(jidparams)
  if not os.access(config_file,os.R_OK):
    config.write(open(config_file,'w'))
    print "Please edit",filename,"to include a valid JID for sending messages"
    return None
  
  config.read(config_file)
  jidparams = dict(config.items(profile))
  return jidparams

