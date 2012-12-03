"""Error messages handled specially by benderjab
"""
import exceptions

__all__ = ['BenderJabBaseError',
           'BotUsageException',
           'BotHelpException',
           'BotArgumentError',
           ]

class BenderJabBaseError(RuntimeError):
    """Base error class for BenderJab specific errors.

    These exceptions are to be used as application errors
    returned back to the user.
    """
    pass

class BotUsageException(BenderJabBaseError):
    pass

class BotHelpException(BenderJabBaseError):
    """abort parsing and return help.

    This really isn't an error, but the way argparse
    wants to handle Help and Usage makes it easier
    to implement as an exception.
    """
    pass

class BotArgumentError(BenderJabBaseError):
    pass
