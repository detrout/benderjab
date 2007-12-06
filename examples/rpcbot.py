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
    def __init__(self):
        super(SumBot, self).__init__()
        
        def sumMethod(*args):
            return reduce(operator.add, args)
    
        self.register_function(sumMethod)
        
    def _parser(self, msg, who):
        if re.match("help", msg):
            reply = "I respond to xml-rpc messages adding a list of numbers together"
        else:
            reply = "I don't do much, but you can try 'help'"
        return reply
          
if __name__ == "__main__":
    bot = SumBot()
    sys.exit(bot.main(sys.argv[1:]))
