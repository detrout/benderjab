#!/usr/bin/env python
#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#
import commands
import errno
from getpass import getpass
import logging
from logging import FileHandler
from optparse import OptionParser
import os
import re
import signal
import sys
import time
import traceback
import types

import xmpp

from benderjab import util
from benderjab import daemon

class JIDMissingResource(RuntimeError):
    """
    XML RPC calls need the full jabber ID + resource to work
    so we might wnat to check to make sure they're present.
    """
    pass

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
    self.authorized_users = None
    self.cl = None
    self.parser = self._parser
    self.eventTasks = []
    
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
      
      self.loglevel = loglevel

      logging.basicConfig(level=loglevel,
                          format='%(asctime)s %(name)-6s %(levelname)-8s %(message)s',
                          filename=self.log_filename)

      logging.info("Debug level set to: %s (%d)" % (levelname, loglevel))

  def _parse_user_list(self, user_list, require_resource=False):
    """
    Convert a space separated list of users into a list of JIDs
    """
    if user_list is None:
        return None
    
    parsed_list = []
    for user in user_list.split():
        jid = util.toJID(user)
        if require_resource and len(jid.resource) == 0:
            msg = 'need a resource identifier for the Jabber ID'
            raise JIDMissingResource(msg)
        parsed_list.append(jid)
    return parsed_list
            
  def check_authorization(self, who):
    """
    Check our sender against the allowed list of users
    """
    if self.authorized_users is None:
        return True
    
    for user in self.authorized_users:
      if who.bareMatch(user):
        return True
    return False
    
  def _check_required_option(self, name):
    """
    Check cfg for a required option
    """
    if self.cfg[name] is None:
      errmsg="Please specify %s in the configfile" % (name)
      logging.fatal(errmsg)
      raise RuntimeError(errmsg)
    else:
      return self.cfg[name]
  
  def read_config(self, section=None, configfile=None):
      """
      Grab all the parameters from [section] in configfile 
      (and check in [hostname] and [default] as well)
      """
      if section is None:
          section = self.section
      if configfile is None:
          configfile = self.configfile
          
      self.cfg.update(util.get_config(section, configfile))
      
      self.authorized_users = self._parse_user_list(self.cfg.get('authorized_users', None))
  
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
  
  def _get_jid(self):
      return self.cfg['jid']
  def _set_jid(self, jid):
      if self.cl is None:
          self.cfg['jid'] = util.toJID(jid)
      else:
          raise ValueError("Already logged in, can't change jabber ID")
  jid = property(_get_jid, _set_jid, doc="set jabber ID")
  
  def _get_resource(self):
      return self.cfg['resource']
  def _set_resource(self, resource):
      if self.cl is None:
          self.cfg['resource'] = resource
      else:
          raise ValueError("Already logged in, can't change resource")
  resource = property(_get_resource, _set_resource, doc="set jabber resource ID")
     
  def on_sigterm(self, signalnum, frame):
      raise KeyboardInterrupt("SIGTERM")
      
  def register_signal_handlers(self):
      signal.signal(signal.SIGTERM, self.on_sigterm)
      
  def main(self, args=None):
      """
      Parse command line, and start application
      """
      if args is None:
          args = sys.argv[1:]
      saved_args = args
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
          
  def daemonize(self):
      """
      Things to do when detaching from the terminal
      """

      print 'detaching from console'
      daemon.createDaemon()
      
  def start(self, daemonize):
      if daemon.checkPidFileIsSafeToRun(self.pid_filename):
          if daemonize:
              self.daemonize()
          self.configure_logging()
          self.register_signal_handlers()
          daemon.writePidFile(self.pid_filename)
          logging.critical("starting up")
          try:
              self.run()
          except (KeyboardInterrupt, SystemExit):
              pass
          #except Exception, e:
          #    errmsg = u'Fatal Exception: ' + unicode(e)
          #    print errmsg
              
          # indicate shutting down
          logging.warn("shutting down. (%d)" % (os.getpid()))
          daemon.removePidFile(self.pid_filename)
          logging.shutdown()
  
  def stop(self):
      if os.path.exists(self.pid_filename):
          pid = daemon.readPidFile(self.pid_filename)
          if pid is None:
              return
      
          try:
              os.kill(pid, signal.SIGTERM)
          except OSError, (code, text):
              if code == errno.ESRCH:
                  errmsg = "PID %d isn't running" % (pid)
                  print errmsg
      else:
          msg = "No pidfile at %s, assuming nothing is running"
          logging.info(msg % (self.pid_filename))
  
  def restart(self, daemonize):
      self.stop()
      self.start(daemonize)
      
      
  def logon(self, jid=None, password=None, resource=None):
    """connect to server"""
    if jid is not None:
        self.cfg['jid'] = util.toJID(jid)
    if password is not None:
        self.cfg['password'] = password
    if resource is not None:
        self.cfg['resource'] = resource
        
    if self.cfg['jid'] is None:
        raise ValueError("please set a jabber ID before logging in")
    if self.cfg['password'] is None:
        raise ValueError("please set a password before logging in")
    
    jid = util.toJID(self.cfg['jid'])    
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
      tojid = util.toJID(jid)
      self.cl.send(xmpp.protocol.Message(tojid,typ='chat',body=unicode(message)))

  def messageCB(self, conn, msg):
    """Simple handling of messages
    """
    who = msg.getFrom()
    body = msg.getBody()
     
    if body is None:
        #logging.debug(u"FROM: <%s>: sent empty packet" %(unicode(who)))
        return None
    elif self.check_authorization(who):
        try:
            logging.debug(u"FROM: <%s> " % (unicode(who)) + unicode(body))
            reply = self.parser(body, who)
        except Exception, e:
            reply = u"Exception: " + unicode(e)
            logging.error(u"Exception in messageCB. "+unicode(e))
            logging.debug(traceback.format_exc())
    else:
        reply = u"Authorization Error."

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
    elif re.match("Exception:", message):
      logging.warning("Received Exception: " + message)
      reply = None
    else:
      reply = "I have no idea what \""+message+"\" means."
    return reply

  def presenceCB(self, conn, msg):
    try:
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
    except Exception, e:
      logging.error("Exception in presenceCB " + str(e))
      logging.debug(traceback.format_exc())


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

    try:
        step_timeout = self.cfg['timeout']
        if timeout is None:
            while self.step(self.cl, step_timeout):
                pass
        else:
            tstart = time.time()
            while self.step(self.cl, step_timeout) and timeout > 0:
                tnow = time.time()
                timeout -= (tnow - tstart)
                tstart = tnow
    except Exception, e:
      logging.error("Fatal Exception " + str(e))
      logging.debug(traceback.format_exc())
  
    return

  def disconnect(self):
    self.cl.disconnect()

if __name__ == "__main__":
    bot = BenderJab()
    bot.main()
