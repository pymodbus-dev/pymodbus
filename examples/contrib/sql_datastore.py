"""Datastore using SQL."""
# pylint: disable=missing-type-doc
try:
    import sqlalchemy
    import sqlalchemy.types as sqltypes
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.schema import UniqueConstraint
    from sqlalchemy.sql import and_
    from sqlalchemy.sql.expression import bindparam
except ImportError:
    pass

from pymodbus.datastore import ModbusBaseSlaveContext
from pymodbus.logging import Log


# --------------------------------------------------------------------------- #
# Context
# --------------------------------------------------------------------------- #
class SqlSlaveContext(ModbusBaseSlaveContext):
    """This creates a modbus data model with each data access in its a block."""

    def __init__(self, *_args, **kwargs):
        """Initialize the datastores.

        :param kwargs: Each element is a ModbusDataBlock
        """
        self._engine = None
        self._metadata = None
        self._table = None
        self._connection = None
        self.table = kwargs.get("table", "pymodbus")
        self.database = kwargs.get("database", "sqlite:///:memory:")
        self._db_create(self.table, self.database)

    def __str__(self):
        """Return a string representation of the context.

        :returns: A string representation of the context
        """
        return "Modbus Slave Context"

    def reset(self):
        """Reset all the datastores to their default values."""
        self._metadata.drop_all(None)
        self._db_create(self.table, self.database)

    def validate(self, fc, address, count=1):
        """Validate the request to make sure it is in range.

        :param fc: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        address = address + 1  # section 4.4 of specification
        Log.debug("validate[{}] {}:{}", fc, address, count)
        return self._validate(self.decode(fc), address, count)

    def getValues(self, fc, address, count=1):
        """Get `count` values from datastore.

        :param fc: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        address = address + 1  # section 4.4 of specification
        Log.debug("get-values[{}] {}:{}", fc, address, count)
        return self._get(self.decode(fc), address, count)

    def setValues(self, fc, address, values, update=True):
        """Set the datastore with the supplied values.

        :param fc: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        :param update: Update existing register in the db
        """
        address = address + 1  # section 4.4 of specification
        Log.debug("set-values[{}] {}:{}", fc, address, len(values))
        if update:
            self._update(self.decode(fc), address, values)
        else:
            self._set(self.decode(fc), address, values)

    # ----------------------------------------------------------------------- #
    # Sqlite Helper Methods
    # ----------------------------------------------------------------------- #
    def _db_create(self, table, database):
        """Initialize the database and handles.

        :param table: The table name to create
        :param database: The database uri to use
        """
        self._engine = sqlalchemy.create_engine(
            database,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self._metadata = sqlalchemy.MetaData(self._engine)
        self._table = sqlalchemy.Table(
            table,
            self._metadata,
            sqlalchemy.Column("type", sqltypes.String(1)),
            sqlalchemy.Column("index", sqltypes.Integer),
            sqlalchemy.Column("value", sqltypes.Integer),
            UniqueConstraint("type", "index", name="key"),
        )
        self._table.create(self._engine)
        self._connection = self._engine.connect()

    def _get(self, sqltype, offset, count):
        """Get."""
        query = self._table.select(
            and_(
                self._table.c.type == sqltype,
                self._table.c.index >= offset,
                self._table.c.index <= offset + count - 1,
            )
        )
        query = query.order_by(self._table.c.index.asc())
        result = self._connection.execute(query).fetchall()
        return [row.value for row in result]

    def _build_set(self, sqltype, offset, values, prefix=""):
        """Generate the sql update context."""
        result = []
        for index, value in enumerate(values):
            result.append(
                {
                    prefix + "type": sqltype,
                    prefix + "index": offset + index,
                    "value": value,
                }
            )
        return result

    def _check(self, sqltype, offset, _values):
        """Check."""
        result = self._get(sqltype, offset, count=1)
        return (
            False  # pylint: disable=simplifiable-if-expression
            if len(result) > 0
            else True
        )

    def _set(self, sqltype, offset, values):
        """Set."""
        if self._check(sqltype, offset, values):
            context = self._build_set(sqltype, offset, values)
            query = self._table.insert()
            result = self._connection.execute(query, context)
            return result.rowcount == len(values)
        return False

    def _update(self, sqltype, offset, values):
        """Update."""
        context = self._build_set(sqltype, offset, values, prefix="x_")
        query = self._table.update().values(value="value")
        query = query.where(
            and_(
                self._table.c.type == bindparam("x_type"),
                self._table.c.index == bindparam("x_index"),
            )
        )
        result = self._connection.execute(query, context)
        return result.rowcount == len(values)

    def _validate(self, sqltype, offset, count):
        """Validate."""
        query = self._table.select(
            and_(
                self._table.c.type == sqltype,
                self._table.c.index >= offset,
                self._table.c.index <= offset + count - 1,
            )
        )
        result = self._connection.execute(query).fetchall()
        return len(result) == count
