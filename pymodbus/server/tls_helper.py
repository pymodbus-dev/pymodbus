"""
TLS helper for Modbus TLS Server
------------------------------------------

"""
import ssl

def sslctx_provider(sslctx=None, certfile=None, keyfile=None, password=None,
                    reqclicert=False):
    """ Provide the SSLContext for ModbusTlsServer

    If the user defined SSLContext is not passed in, sslctx_provider will
    produce a default one.

    :param sslctx: The user defined SSLContext to use for TLS (default None and
                   auto create)
    :param certfile: The cert file path for TLS (used if sslctx is None)
    :param keyfile: The key file path for TLS (used if sslctx is None)
    :param password: The password for for decrypting the private key file
    :param reqclicert: Force the sever request client's certificate
    """
    if sslctx is None:
        # According to MODBUS/TCP Security Protocol Specification, it is
        # TLSv2 at least
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        sslctx.load_cert_chain(certfile=certfile, keyfile=keyfile,
                               password=password)

    if reqclicert:
        sslctx.verify_mode = ssl.CERT_REQUIRED

    return sslctx
