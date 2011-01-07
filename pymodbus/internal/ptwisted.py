'''
A collection of twisted utility code
'''
from twisted.cred import portal, checkers
from twisted.conch import manhole, manhole_ssh
from twisted.conch.insults import insults

def InstallManagementConsole(namespace, users={'admin':'admin'}, port=503):
    ''' Helper method to start an ssh management console
        for the modbus server.

    :param namespace: The data to constrain the server to
    :param users: The users to login with
    :param port: The port to host the server on
    '''
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

def InstallSpecializedReactor():
    '''
    This attempts to install a reactor specialized for the given
    operating system.

    :returns: True if a specialized reactor was installed, False otherwise
    '''
    from twisted.internet import epollreactor, kqreactor, iocpreactor
    for reactor in [epollreactor, kqreactor, iocpreactor]:
        try:
            reactor.install()
            _logger.debug("Installed %s" % reactor.__name__)
            return True
        except: pass
    _logger.debug("No specialized reactor was installed")
    return False

