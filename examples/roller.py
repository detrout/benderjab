#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import re
import sys

from benderjab.bot import BenderJab

# this came from the pyparsing wiki http://pyparsing.wikispaces.com/Examples
# slightly modified
import dice2

def parser(s, who=None):
  try:
    if re.match("roll", s):
      return dice2.dice(s[4:])
  except Exception as e:
    return "failed:"+str(e)

def loop_reporter():
  print(".")

def main():
  bot = BenderJab('bender@ghic.org')
  bot.parser = parser
  #bot.eventTasks.append(loop_reporter)
  bot.logon()
  bot.eventLoop()
  return 0

if __name__ == "__main__":
  sys.exit(main())
