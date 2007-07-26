#!/usr/bin/env python

import re
import sys
import xmpp

from benderjab.benderjab import BenderFactory

def read_linux_uptime():
  """So I don't have to keep retyping /proc/loadavg
  """
  return open("/proc/loadavg", 'r').read()

def parse_uptime(loadavg):
  """
  parse loadavg for the 1,5,15 minute averages and the number of processes
  """
  loadavg = read_linux_uptime().split()
  one = float(loadavg[0])
  five = float(loadavg[1])
  fifteen = float(loadavg[2])
  process = loadavg[3]
  return (one,five,fifteen,process)

def parser(message, who=None):
  reply = ""
  try:
    if re.match("uptime", message):
      reply = read_linux_uptime()
    elif re.match("time", message):
      reply = "Server time is "+time.asctime()
    else:
      reply = "Unknown command:", message
  except Exception, e:
    return "failed:"+str(e)
  return reply

class update_presence(object):
  def __init__(self):
    self.presence = ''
    
  def __call__(self, bot):
    loadavg = read_linux_uptime()
    one,five,fifteen,process = parse_uptime(loadavg)
    if one > 10.0:
      presence = 'xa'
    elif one > 5.0:
      presence = 'dnd'
    elif one > 1.0:
      presence = 'away'
    else:
      presence = ''
    if self.presence != presence:
      self.presence = presence
      bot.cl.send(xmpp.Presence(show=presence, status=loadavg))

def main(args=None):
  if args is not None and len(args) > 1:
    bot = BenderFactory(args[1])
  else:
    bot = BenderFactory()

  # lets not overload already overloaded systems, wait 5 seconds between
  # updates
  bot.parser = parser
  bot.eventTasks.append(update_presence())
  bot.logon()
  bot.eventLoop()
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv))
