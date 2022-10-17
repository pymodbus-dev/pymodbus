__all__ = ["apply_pymodbus_logging_config"]


import logging
from logging import NullHandler


# ---------------------------------------------------------------------------#
#  Block unhandled logging
# ---------------------------------------------------------------------------#
logging.getLogger(__name__).addHandler(NullHandler())


def apply_pymodbus_logging_config():
    logging.basicConfig(
        format="%(asctime)s %(levelname)-5s %(module)s:%(lineno)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.WARNING,
    )
