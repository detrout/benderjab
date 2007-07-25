#!/usr/bin/env python

import re
import sys

from benderjab.benderjab import BenderJab

# this came from the pyparsing wiki http://pyparsing.wikispaces.com/Examples
# slightly modified
import dice2

def parser(s, who=None):
  try:
    if re.match("roll", s):
      return dice2.dice(s[4:])
  except Exception, e:
    return "failed:"+str(e)

def loop_reporter():
  print "."

def main():
  bot = BenderJab('bender@ghic.org')
  bot.parser = parser
  #bot.eventTasks.append(loop_reporter)
  bot.logon()
  bot.eventLoop()
  return 0

if __name__ == "__main__":
  sys.exit(main())
