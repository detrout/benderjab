#!/usr/bin/env python
import os
import re
import sys

import aiml

from benderjab.benderjab import BenderFactory

class AimlBot(object):
  def __init__(self, startup, brain=None, commands=None):
    """Initalize an Aiml bot from the AIML file at startup

    you can pass in a command if the bot needs a specific AIML command
    to get started
    """
    self.kernel = aiml.Kernel()
    self._load(startup, brain, commands)

  def _load(self, startup, brain=None, commands=None):
    """AIML loading code
    """
    self.startup_path, self.startup = os.path.split(startup)
    self.brain = self._brainname(brain, self.startup)
    if commands is None:
      commands = ""
    self.commands = commands

    if os.path.isfile(self.brain):
      self.kernel.bootstrap(brainFile=self.brain)
    else:
      curdir = os.getcwd()
      if len(self.startup_path) > 0:
        os.chdir(self.startup_path)
      self.kernel.bootstrap(learnFiles = self.startup, commands=self.commands)
      os.chdir(curdir)

  def cacheBrain(self, brain=None):
    """save parsed AIML files, 
    if brain is None use the default based on the startup filename
    if brain isn't None, use it, and save the brain name
    """
    if brain is None:
      self.brain = brain
    self.kernel.saveBrain(self.brain)

  def reloadBrain(self, startup=None, commands=None):
    """Reload an AIML file

    if startup is not none use that file instead
    """
    if startup is not None:
      self._load(self.startup, self.commands)
    else:
      self._load(os.path.join(self.startup_path, self.startup), self.commands)

  def read_eval_loop(self, name=None):
    """start a simple test read eval loop"""
    try:
      while True:
         line = input("> ")
         print(self.respond(line, name))
    except (EOFError, KeyboardInterrupt) as e:
      print("[END OF LINE]")

  def respond(self, line, name=None):
    """
    Call the kernel's respond method, catching the case of no response
    """
    response = self.kernel.respond(line, name)
    if len(response) == 0:
      return "<blank look>"
    else:
      return response

  def _brainname(self, brain, startup):
    """Return a brainname derived from brain and startup filenames

    Aka use brain but if its none come up with a name from startup.
    """
    if brain is not None:
      return brain
    rootname,ext = os.path.splitext(startup)
    return rootname+".brn"


class parser(object):
  def __init__(self, startup, brainfile):
    self.bot = AimlBot(startup, brainfile)

  def __call__(self, s, who):
    return self.bot.respond(s, str(who))


def main(args):
  if len(args) < 1:
    startup = "aiml/empty.xml"
  else:
    startup = args[0]
  brainfile = None
  if len(args) == 2:
    brainfile = args[1]

  bot = BenderFactory('demobot')
  bot.parser = parser(startup, brainfile)
  if brainfile is not None:
    bot.parser.cacheBrain()
  bot.logon()
  bot.eventLoop()
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
