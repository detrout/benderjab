"""Customizes argparse to work with the benderjab message loop

The default argparse expects to be running in a terminal
like environment. so expects to be able to write to a stream
instead of returning values.
"""

from argparse import ArgumentParser, Action, HelpFormatter, \
     Namespace, ArgumentError, \
     SUPPRESS, _UNRECOGNIZED_ARGS_ATTR
from benderjab.exceptions import *

class BotArgumentParser(ArgumentParser):
    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 version=None,
                 parents=[],
                 formatter_class=HelpFormatter,
                 prefix_chars='-',
                 fromfile_prefix_chars=None,
                 argument_default=None,
                 conflict_handler='error',
                 add_help=True):
        super(BotArgumentParser, self).__init__(
            prog='BotCommands',
            usage=usage,
            description=description,
            epilog=epilog,
            version=version,
            parents=parents,
            formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=None,
            argument_default=None,
            conflict_handler=conflict_handler,
            add_help=add_help)

        #self.register('action', 'help', BotHelpAction)

    def print_usage(self, file=None):
        raise BotUsageException( self.format_usage() )

    def print_help(self, file=None):
        raise BotHelpException(self.format_help())

    def exit(self, status=0, message=None):
        """Don't actually cause the bot to exit"""
        pass

    def error(self, message):
        usage = self.format_usage() + '\n%s' % (message,)
        raise BotUsageException(usage)

    def parse_known_args(self, args=None, namespace=None):
        if args is None:
            raise BotUsageExceptions("No commands to process")
        else:
            args = list(args)

        if namespace is None:
            namespace = Namespace()

        for action in self._actions:
            if action.dest is not SUPPRESS:
                if not hasattr(namespace, action.dest):
                    if action.default is not SUPPRESS:
                        setattr(namespace, action.dest, action.default)

        for dest in self._defaults:
            if not hasattr(namespace, dest):
                setattr(namespace, dest, self._defaults[dest])

        try:
            namespace, args = self._parse_known_args(args, namespace)
            if hasattr(namespace, _UNRECOGNIZED_ARGS_ATTR):
                args.extend(getattr(namespace, _UNRECOGNIZED_ARGS_ATTR))
                delattr(namespace, _UNRECOGNIZED_ARGS_ATTR)
            return namespace, args
        except ArgumentError as e:
            raise BotArgumentError(e)


class BotHelpAction(Action):
    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help=None):
        super(BotHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            neargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        return parser.format_help()
