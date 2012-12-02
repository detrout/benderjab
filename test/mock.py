class MockClient(object):
    """Mock a XMPP client
    """
    def __init__(self):
        self.msgs = []

    def send(self, msg):
        self.msgs.append(msg)

