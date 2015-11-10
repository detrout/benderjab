"""Probe bot

I was looking through the examples in XMPP: A Definitive Guide,
and wanted an easier way to try some of their examples.
"""
from lxml.etree import fromstring, dump
import xmpp
import shlex
from benderjab import bot
from benderjab.util import get_config, toJID
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

    def logon(self, jid=None, password=None, resource=None):
        super(ProbeBot, self).logon(jid, password, resource)
        print("registering")
        self.cl.RegisterHandler('iq', self.iqCB)


    def list_commands(self, arg):
        return "Available commands: " + ", ".join(list(self.commands.keys()))

    def messageCB(self, conn, msg):
        tree = fromstring(str(msg))
        dump(tree)
        return super(ProbeBot, self).messageCB(conn, msg)

    def presenceCB(self, conn, msg):
        tree = fromstring(str(msg))
        dump(tree)
        return super(ProbeBot, self).presenceCB(conn, msg)

    def iqCB(self, dis, stanza):
        #print "dis:", unicode(dis)
        tree = fromstring(str(stanza))
        dump(tree)

    def format_help(self, args):
        return self.argparse.format_help()

    def _parser(self, message, who):
        if message:
            cmdline = shlex.split(message)
            args = self.argparse.parse_args(cmdline)
            print("args", args)
            args.frm = who
            if args.func:
                return args.func(args)
            return "Didn't understand:" + str(message)

    def command(self, name, **kwargs):
        def wrapper(func):
            if not hasattr(func, SUBPARSER):
                func.subparser = self.subparsers.add_parser(name, **kwargs)
                func.subparser.prog = name
                func.subparser.set_defaults(func=func)
                func.subparser.set_defaults(bot=self)
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
@bot.command('echo', help="return your message")
def echo(args):
    if args.strings:
        return 'You sent:'+' '.join((str(s) for s in args.strings))
    return 'Nothing! You sent Nothing!'

@bot.argument('dice', nargs='*', type=str,
              help='Specify a die formula. e.g. 2d4 + 2')
@bot.command('roll', help="Roll D&D-esque dice")
def roll(args):
    if args.dice:
        return dice(' '.join(args.dice))
    parser = getattr(roll, SUBPARSER)
    return parser.format_usage()

@bot.argument('-w', '--who', help="specify JID to query")
@bot.argument('--node', nargs=1, help="specify a node attribute")
@bot.command('disco-items', help="send a disco#items query")
def disco_info(args):
    if not args.who:
        return self.subparser.format_usage()
    who = toJID(args.who)
    q = xmpp.Iq(typ="get",
                queryNS='http://jabber.org/protocol/disco#items',
                to=who)
    if args.node:
        q.setTagAttr('query', 'node', args.node[0])
    args.bot.cl.send(q)
    return "Sent items query"

@bot.argument('-w', '--who', help="specify JID to query")
@bot.argument('--node', nargs=1, help="specify a node attribute")
@bot.command('disco-info', help="send a disco#info query")
def disco_info(args):
    if not args.who:
        return self.subparser.format_usage()
    who = toJID(args.who)

    q = xmpp.Iq(typ="get",
                queryNS='http://jabber.org/protocol/disco#info',
                to=who)
    if args.node:
        q.setTagAttr('query', 'node', args.node[0])
    tree = fromstring(str(q))
    print("--disco-info--")
    dump(tree)
    args.bot.cl.send(q)
    return "Sent info query"

@bot.command('form', help="send me a form")
def form(args):
    form = '''<captcha xmlns="urn:xmpp:captcha">
        <x xmlns="jabber:x:data" type="form">
        <title>A form!</title>
        <instructions>Fill in the form</instructions>
        <field label="Text input" type="text_single" var="field-1"/>
        <field label="Pick one" type="list-single" var="field-2">
          <option label="First"><value>opt-1</value></option>
          <option label="Second"><value>opt-2</value></option>
        </field>
        </x>
        </captcha>'''
    f = xmpp.Message(
        to=args.frm,
        payload=[xmpp.simplexml.XML2Node('<body>Form attached</body>'),
                 xmpp.simplexml.XML2Node(form)])
    tree = fromstring(str(f))
    print "--form--"
    dump(tree)
    args.bot.cl.send(f)
    return "I hope you like it"

@bot.command('who', help="list who is online")
def who(args):
    roster = args.bot.cl.getRoster()
    reply = []
    for jid in roster.keys():
        resources = roster.getResources(jid)
        if resources:
            reply.append(str(jid))
            for resource in resources:
                reply.append(str('\t'+jid+'/'+resource))

    return "\n".join(reply)


if __name__ == "__main__":
    bot.main()
