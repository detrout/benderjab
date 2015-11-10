#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
# Time delay code by Brandon King; LGPL 2.1 still
import re
import sys
import xmpp

import datetime

from benderjab.bot import BenderFactory

__message_list = []


class TimeDelayMessage(object):
  
  def __init__(self, message, who, seconds=0):
    self.message = message,
    self.who = who
    self.seconds = seconds
    self.delta = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
  

def remindme(message, who):
  mo = re.search("[0-9]+", message)
  if not mo:
    return "useage: remindme <seconds> <message>"
  
  seconds = int(message[mo.start():mo.end()])
  msg = message[mo.end()+1:]
  
  print(msg)
  __message_list.append(TimeDelayMessage(msg, who, seconds))
  
  return "I will remind you in %s seconds." % (seconds)
  

def parser(message, who=None):
  reply = ""
  try:
    if re.match("hello", message):
      reply = "world"
    elif re.match("remindme", message):
      reply = remindme(message, who)
    else:
      reply = "Unknown command:", message
  except Exception as e:
    return "failed:"+str(e)
  return reply


def handle_delayed_messages(bot):
  """
  If there are any message in the queue where it is now time to
  respond, respond to them.
  """
  global __message_list
  
  # Don't do anything if we don't need to.
  if len(__message_list) == 0:
    print('Delay: Nothing to do.')
    return
  
  # Get list of messages that need to be sent.
  cur_dt = datetime.datetime.now()
  to_process_list = [ msg for msg in __message_list if (msg.delta - cur_dt).days < 0 ]
  for msg in __message_list:
    print('%s - %s = %s' % (msg.delta, cur_dt, (msg.delta - cur_dt).seconds))
  
  print('Delay: Found %s message to process.' % (len(to_process_list)))
  # Nothing to do yet.
  if len(to_process_list) == 0:
    return
  
  # Remove messages from queue before processing.
  for msg in to_process_list:
    __message_list.remove(msg)
    #Send message
    print('Delay: Sending message to %s: %s' % (msg.who, msg.message))
    print('preping: %s' % (msg.message))
    bot.cl.send(xmpp.Message(msg.who, "Reminder:" + msg.message[0], typ="chat"))
  
  
def main(args=None):
  if args is not None and len(args) > 1:
    bot = BenderFactory(args[1])
  else:
    bot = BenderFactory()

  # lets not overload already overloaded systems, wait 5 seconds between
  # updates
  bot.parser = parser
  #bot.eventTasks.append(update_presence())
  bot.eventTasks.append(handle_delayed_messages)
  bot.logon()
  bot.eventLoop()
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv))
