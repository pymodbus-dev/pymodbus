"""Define Datastore."""
from pymodbus.datastore.database.redis_datastore import RedisSlaveContext
from pymodbus.datastore.database.sql_datastore import SqlSlaveContext


# ---------------------------------------------------------------------------#
#  Exported symbols
# ---------------------------------------------------------------------------#
__all__ = ["SqlSlaveContext", "RedisSlaveContext"]
