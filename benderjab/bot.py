#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import commands
import errno
from getpass import getpass
import logging
from optparse import OptionParser
import os
import re
import signal
import sys
import time
import types

import xmpp

from benderjab.util import toJID, get_password, get_config
from benderjab import daemon
 
class BenderJab(object):
  """Base class for a simple jabber bot

  self.eventTasks - list of things to do after an event timeout
  """
  # override to change default config file
  configfile = "~/.benderjab"
  
  def __init__(self, section=None, configfile=None):
    """Initialize our bot
    """
    self.section = section
    if configfile is not None:
        self.configfile = configfile
    
    # set defaults
    self.cfg = {}
    self.cfg['jid'] = None
    self.cfg['password'] = None
    self.cfg['resource'] = "BenderJab"
    # number of seconds to wait in each poll step
    self.cfg['timeout'] = 5
    self.cfg['pid'] = "/tmp/%(jid)s.%(resource)s.pid"
    self.cfg['log'] = "/tmp/%(jid)s.%(resource)s.log"
    self.cfg['loglevel'] = "WARNING"
        
    # set defaults for things that can't be set from a config file
    self.cl = None
    self.parser = self._parser
    self.eventTasks = []
    self.log = logging.getLogger('benderjab.bot')
    
  def configure_logging(self):
      """
      Set up log
      """
      levelname = self.cfg['loglevel']
      
      if levelname is None:
          loglevel = logging.DEBUG
      else:
          levename = levelname.upper()
          if levelname == 'DEBUG':
              loglevel = logging.DEBUG
          elif levelname == 'INFO':
              loglevel = logging.INFO
          elif levelname == 'WARNING':
              loglevel = logging.WARNING
          elif levelname == 'ERROR':
              loglevel = logging.ERROR
          elif levelname == 'CRITICAL':
              loglevel = logging.CRITICAL
          elif levelname == 'FATAL':
              loglevel = logging.FATAL
          else:
              loglevel = logging.DEBUG
      
      print levelname, loglevel
      logging.basicConfig(level=loglevel,
                          format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                          filename=self.log_filename,
                          filemode='w')

  def read_config(self, section=None, configfile=None):
      """
      Grab all the parameters from [section] in configfile 
      (and check in [hostname] and [default] as well)
      """
      if section is None:
          section = self.section
      if configfile is None:
          configfile = self.configfile
          
      self.cfg.update(get_config(section, configfile))
  
  def command_line_parser(self):
      """
      Return a configured parser object
      """
      usage = "usage: %prog profile_name"
      parser = OptionParser()

      parser.add_option('-j', '--jid', dest="jid", default=None,
                        help="the jabber id we should connect as")
      parser.add_option('--resource', dest='resource', default=None,
                        help='specify what resource name to use')
                        
      parser.add_option('--start', dest='action', action='store_const', const='start',
                        default='start',
                        help='start the daemon (default)')
      parser.add_option('--stop', dest='action', action='store_const', const='stop',
                        default='start',
                        help='stop the daemon')
      parser.add_option('--restart', dest='action', action='store_const', const='restart',
                        default='start',
                        help='kill any currently running daemon, and then start')
      parser.add_option('-c','--config', dest='configfile',default=None,
                        help='specify a configuration file')
      parser.add_option('-s', '--section', dest='section', default=None,
                        help="specify which section of the config file to use.")
      parser.add_option('-n', '--nodaemon', dest='daemon', action='store_false',
                        default=True,
                        help="Don't run in background")
      return parser
  
  def _get_cfg_subset(self):
      """
      return a subset of config options for formatting of our *_filename functions
      """
      return { 'jid': self.cfg['jid'],
               'resource': self.cfg['resource']}
               
  def _get_pid_filename(self):
      """
      format the pid filename
      """
      return self.cfg['pid'] % (self._get_cfg_subset())
  pid_filename = property(_get_pid_filename, doc="name of file to store our process ID in")
  
  def _get_log_filename(self):
      """
      Format the log filename
      """
      return self.cfg['log'] % (self._get_cfg_subset())
  log_filename = property(_get_log_filename, doc="name of file to store our log in")
      
  def main(self, args=None):
      """
      Parse command line, and start application
      """
      if args is None:
          args = sys.argv[1:]
      opt_parser = self.command_line_parser()
      opt, args = opt_parser.parse_args(args)
      
      if opt.configfile is not None:
          if not os.path.exists(opt.configfile):
              opt_parser.error("unable to find %s" % (opt.options.configfile))
      self.read_config(opt.section, opt.configfile)
      
      if opt.jid is not None:
          self.cfg['jid'] = opt.jid
      if opt.resource is not None:
          self.cfg['resource'] = opt.resource
          
      if opt.action == 'start':
          self.start(opt.daemon)
      elif opt.action ==  'stop':
          self.stop()
      elif opt.action == 'restart':
          self.restart(opt.daemon)
      
  def start(self, daemonize):
      if daemon.checkPidFileIsSafeToRun(self.pid_filename):
          if daemonize:
              daemon.createDaemon()
          daemon.writePidFile(self.pid_filename)
          self.configure_logging()
          self.run()
  
  def stop(self):
      pid = daemon.readPidFile(self.pid_filename)
      if pid is None:
          return
      
      try:
          os.kill(pid, signal.SIGTERM)
      except OSError, (code, text):
          if code == errno.ESRCH:
              logging.warning("PID %d isn't running" % (pid))
      os.unlink(self.pid_filename)
  
  def restart(self, daemonize):
      self.stop()
      self.start(daemonize)
      
      
  def logon(self, jid=None, password=None, resource=None):
    """connect to server"""
    if jid is not None:
        self.cfg['jid'] = toJID(jid)
    if password is not None:
        self.cfg['password'] = password
    if resource is not None:
        self.cfg['resource'] = resource
        
    if self.cfg['jid'] is None:
        raise ValueError("please set a jabber ID before logging in")
    if self.cfg['password'] is None:
        raise ValueError("please set a password before logging in")
    
    jid = toJID(self.cfg['jid'])    
    self.cl = xmpp.Client(jid.getDomain(), debug=[])
    # if you have dnspython installed and use_srv is True
    # the dns service discovery lookup seems to fail.
    self.cl.connect(use_srv=False)

    auth_state = self.cl.auth(jid.getNode(), self.cfg['password'], self.cfg['resource'])
    if auth_state is None:
      # auth failed
      self.log.error(u"couldn't authenticate with"+unicode(self.jid))
      # probably want a better exception here
      raise RuntimeError(self.cl.lastErr)

    # tell the xmpp client that we're ready to handle things
    self.cl.RegisterHandler('message', self.messageCB)
    self.cl.RegisterHandler('presence', self.presenceCB)
  
    # announce our existence to the server
    self.cl.getRoster()
    self.cl.sendInitPresence()
    # not needed but lets me muck around with the client from interpreter
    return self.cl
  
  def send(self, jid, message):
      """
      Send a message to specified user
      """
      logging.debug(u"TO: <%s> " % (unicode(jid)) + unicode(message))
      tojid = toJID(jid)
      self.cl.send(xmpp.protocol.Message(tojid,typ='chat',body=unicode(message)))

  def messageCB(self, conn, msg):
    """Simple handling of messages
    """
    who = msg.getFrom()
    body = msg.getBody()
     
    if body is None:
      return
    try:
      logging.debug(u"FROM: <%s> " % (unicode(who)) + unicode(body))
      reply = self.parser(body, who)
    except Exception, e:
      reply = u"failed: " + unicode(e)
      self.log.error("Exception in messageCB. "+unicode(e))

    self.send(who, reply)
          
  def _parser(self, message, who):
    """Default parser function, 
    overide this or replace self.parser with a different function
    to do something more useful
    """
    # some default commands
    if re.match("help", message):
      reply = "I'm sooo not helpful"
    elif re.match("time", message):
      reply = "Server time is "+time.asctime()
    elif re.match("uptime", message):
      reply = commands.getoutput("uptime")
    else:
      reply = "I have no idea what \""+message+"\" means."
    return reply

  def presenceCB(self, conn, msg):
    presence_type = msg.getType()
    who = msg.getFrom()
    # This code provides for a fairly promiscous bot
    # a more secure bot should check an auth list and accept deny
    # based on the incoming who JID
    if presence_type == "subscribe":
      # Tell the server that we accept their subscription request
      conn.send(xmpp.Presence(to=who, typ='subscribed'))
      # Ask to be their contact too
      conn.send(xmpp.Presence(to=who, typ='subscribe'))
      # Be friendly
      conn.send(xmpp.Message(who, "hi " + who.getNode(), typ='chat'))
      logging.info("%s subscribed" % (who))
    elif presence_type == "unsubscribe":
      conn.send(xmpp.Message(who, "bye " + who.getNode(), typ='chat'))
      conn.send(xmpp.Presence(to=who, typ='unsubscribed'))
      conn.send(xmpp.Presence(to=who, typ='unsubscribe'))
      logging.info("%s unsubscribed" % (who))

  def step(self, conn, timeout):
    """single step through the event loop"""
    try:
      state = conn.Process(timeout)
      if state is None:
        self.logon()
      for f in self.eventTasks:
        f(self)
      return 1
    except KeyboardInterrupt:
      return 0

  def run(self, timeout=None):
    """
    Enter event loop
    """
    if self.cl is None:
        self.logon()
        
    step_timeout = self.cfg['timeout']
    if timeout is None:
      while self.step(self.cl, step_timeout):
        pass
    else:
      tstart = time.time()
      while self.eventStep(self.cl, step_timeout) and timeout > 0:
        tnow = time.time()
        timeout -= (tnow - tstart)
        tstart = tnow
    return

  def disconnect(self):
    self.cl.disconnect()

if __name__ == "__main__":
    bot = BenderJab()
    bot.main()
