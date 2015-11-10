#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import re
import sys
import xmpp

from benderjab.bot import BenderJab

def main(args=None):
    bot = SysmonBot()
    bot.main(args[1:])
    return 0

class SysmonBot(BenderJab):
    def __init__(self):
        super(SysmonBot, self).__init__()

        self.presence = ''
        self.eventTasks.append(SysmonBot.update_load)
    
    def _parser(self, message, who=None):
        reply = ""

        try:
            if re.match("uptime", message, re.IGNORECASE):
                reply = read_linux_uptime()
            elif re.match("time", message, re.IGNORECASE):
                reply = "Server time is "+time.asctime()
            elif re.match("unknown command", message, re.IGNORECASE):
                reply = ''
            else:
                reply = "Unknown command", message
        except Exception as e:
            return "failed:"+str(e)

        return reply
    
    def update_load(self):
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

if __name__ == "__main__":
  sys.exit(main(sys.argv))
