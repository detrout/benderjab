#!/usr/bin/env python

import operator
import re
import sys
from benderjab import rpc
from benderjab.util import get_config

#
# You can use this bot by doing:
#
# from benderjab import rpc
# 
# cl = rpc.connect( '<.benderjab config file section name>' )
# rpc.call(cl, '<demobot jabber id>', (1,2,3), 'sumMethod')
#
# 
class SumBot(rpc.XmlRpcBot):
    def __init__(self, jid, password, resource='xmlrpc'):
        super(SumBot, self).__init__(jid, password, resource)
        
        def sumMethod(*args):
            return reduce(operator.add, args)
    
        self.register_function(sumMethod)
        
    def _parser(self, msg, who):
        if re.match("help", msg):
            reply = "I respond to xml-rpc messages adding a list of numbers together"
        else:
            reply = "I don't do much, but you can try 'help'"
        return reply
          
def usage():
    print "usage: rpcbot.py <.benderjab conf section name>"
    print

def main(args=None):
    if len(args) != 1:
        usage()
        return 1
    
    config_name = args[0]
    
    bot = SumBot(**get_config(config_name))
    bot.eventLoop()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
