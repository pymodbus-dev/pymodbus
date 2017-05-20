'''
A collection of twisted utility code
'''
from pymodbus.compat import IS_PYTHON2, IS_PYTHON3
if IS_PYTHON2:
    from twisted.cred import portal, checkers
    from twisted.conch import manhole, manhole_ssh
    from twisted.conch.insults import insults

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# Twisted Helper Methods
#---------------------------------------------------------------------------#
def InstallManagementConsole(namespace, users={'admin': 'admin'}, port=503):
    ''' Helper method to start an ssh management console
        for the modbus server.

    :param namespace: The data to constrain the server to
    :param users: The users to login with
    :param port: The port to host the server on
    '''
    if IS_PYTHON3:
        raise NotImplemented("This code currently doesn't work on python3")
    from twisted.internet import reactor

    def build_protocol():
        p = insults.ServerProtocol(manhole.ColoredManhole, namespace)
        return p

    r = manhole_ssh.TerminalRealm()
    r.chainedProtocolFactory = build_protocol
    c = checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
    p = portal.Portal(r, [c])
    factory = manhole_ssh.ConchFactory(p)
    reactor.listenTCP(port, factory)

