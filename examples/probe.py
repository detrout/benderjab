"""Probe bot

I was looking through the examples in XMPP: A Definitive Guide,
and wanted an easier way to try some of their examples.
"""

import shlex
from benderjab import bot
from benderjab.util import get_config
from benderjab.bargparse import BotArgumentParser

from dice2 import dice

SUBPARSER = 'subparser'

class ProbeBot(bot.BenderJab):
    def __init__(self, *args, **kwargs):
        super(ProbeBot, self).__init__(*args, **kwargs)
        self.argparse = BotArgumentParser()
        self.subparsers = self.argparse.add_subparsers()
        helpparser = self.subparsers.add_parser('help')
        helpparser.set_defaults(func=self.format_help)

    def list_commands(self, arg):
        return u"Available commands: " + ", ".join(self.commands.keys())

    def presenceCB(self, conn, msg):
        print "Presence:", str(msg)
        return super(ProbeBot, self).presenceCB(conn, msg)

    def format_help(self, args):
        return self.argparse.format_help()

    def _parser(self, message, who):
        if message:
            cmdline = shlex.split(message)
            args = self.argparse.parse_args(cmdline)
            print "args", args
            if args.func:
                return args.func(args)
            return u"Didn't understand:" + unicode(message)

    def command(self, name):
        def wrapper(func):
            if not hasattr(func, SUBPARSER):
                func.subparser = self.subparsers.add_parser(name)
                func.subparser.prog = name
                func.subparser.set_defaults(func=func)
            return func
        return wrapper

    def argument(self, *args, **kwargs):
        def wrapper(func):
            if not hasattr(func, SUBPARSER):
                raise RuntimeError("Please use bot.command first")
            func.subparser.add_argument(*args, **kwargs)
            return func
        return wrapper

bot = ProbeBot()
@bot.argument('strings', nargs='*', help='echo some text back')
@bot.command('echo')
def echo(args):
    if args.strings:
        return u'You sent:'+u' '.join((unicode(s) for s in args.strings))
    return u'Nothing! You sent Nothing!'

@bot.argument('dice', nargs='*', type=str,
              help='Specify a die formula. e.g. 2d4 + 2')
@bot.command('roll')
def roll(args):
    if args.dice:
        return dice(' '.join(args.dice))

if __name__ == "__main__":
    bot.main()
