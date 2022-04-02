"""
TLS helper for Modbus TLS Client
------------------------------------------

"""
import ssl

def sslctx_provider(sslctx=None, certfile=None, keyfile=None, password=None):
    """ Provide the SSLContext for ModbusTlsClient

    If the user defined SSLContext is not passed in, sslctx_provider will
    produce a default one.

    :param sslctx: The user defined SSLContext to use for TLS (default None and
                   auto create)
    :param certfile: The optional client's cert file path for TLS server request
    :param keyfile: The optional client's key file path for TLS server request
    :param password: The password for for decrypting client's private key file
    """
    if sslctx is None:
        # According to MODBUS/TCP Security Protocol Specification, it is
        # TLSv2 at least
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        sslctx.verify_mode = ssl.CERT_REQUIRED
        sslctx.check_hostname = True

        if certfile and keyfile:
            sslctx.load_cert_chain(certfile=certfile, keyfile=keyfile,
                                   password=password)

    return sslctx
