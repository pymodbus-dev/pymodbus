"""These are a collection of helper methods.

that can be used to save a modbus server context to file for backup,
checkpointing, or any other purpose. There use is very
simple::

    context = server.context
    saver   = JsonDatastoreSaver(context)
    saver.save()

These can then be re-opened by the parsers in the
modbus_mapping module. At the moment, the supported
output formats are:

* csv
* json
* xml

To implement your own, simply subclass ModbusDatastoreSaver
and supply the needed callbacks for your given format:

* handle_store_start(self, store)
* handle_store_end(self, store)
* handle_slave_start(self, slave)
* handle_slave_end(self, slave)
* handle_save_start(self)
* handle_save_end(self)
"""
import json
import xml.etree.ElementTree as xml  # nosec


class ModbusDatastoreSaver:
    """An abstract base class.

    that can be used to implement
    a persistence format for the modbus server context. In
    order to use it, just complete the necessary callbacks
    (SAX style) that your persistence format needs.
    """

    def __init__(self, context, path=None):
        """Initialize a new instance of the saver.

        :param context: The modbus server context
        :param path: The output path to save to
        """
        self.context = context
        self.path = path or "modbus-context-dump"

    def save(self):
        """Save the context to file.

        which calls the various callbacks which the sub classes will implement.
        """
        with open(  # pylint: disable=unspecified-encoding
            self.path, "w"
        ) as self.file_handle:  # pylint: disable=attribute-defined-outside-init
            self.handle_save_start()
            for slave_name, slave in self.context:
                self.handle_slave_start(slave_name)
                for store_name, store in slave.store.iteritems():
                    self.handle_store_start(store_name)
                    self.handle_store_values(iter(store))  # pylint: disable=no-member
                    self.handle_store_end(store_name)
                self.handle_slave_end(slave_name)
            self.handle_save_end()

    # ------------------------------------------------------------
    # predefined state machine callbacks
    # ------------------------------------------------------------
    def handle_save_start(self):
        """Handle save start."""

    def handle_store_start(self, store):
        """Handle store start."""

    def handle_store_end(self, store):
        """Handle store end."""

    def handle_slave_start(self, slave):
        """Handle slave start."""

    def handle_slave_end(self, slave):
        """Handle slave end."""

    def handle_save_end(self):
        """Handle save end."""


# ---------------------------------------------------------------- #
# Implementations of the data store savers
# ---------------------------------------------------------------- #
class JsonDatastoreSaver(ModbusDatastoreSaver):
    """An implementation of the modbus datastore saver.

    that persists the context as a json document.
    """

    _context = None
    _store = None
    _slave = None

    STORE_NAMES = {
        "i": "input-registers",
        "d": "discretes",
        "h": "holding-registers",
        "c": "coils",
    }

    def handle_save_start(self):
        """Handle save start."""
        self._context = {}

    def handle_slave_start(self, slave):
        """Handle slave start."""
        self._context[hex(slave)] = self._slave = {}

    def handle_store_start(self, store):
        """Handle store start."""
        self._store = self.STORE_NAMES[store]

    def handle_store_values(self, values):
        """Handle store values."""
        self._slave[self._store] = dict(values)

    def handle_save_end(self):
        """Handle save end."""
        json.dump(self._context, self.file_handle)


class CsvDatastoreSaver(ModbusDatastoreSaver):
    """An implementation of the modbus datastore saver.

    that persists the context as a csv document.
    """

    _context = None
    _store = None
    _line = None
    NEWLINE = "\r\n"
    HEADER = "slave,store,address,value" + NEWLINE
    STORE_NAMES = {
        "i": "i",
        "d": "d",
        "h": "h",
        "c": "c",
    }

    def handle_save_start(self):
        """Handle save start."""
        self.file_handle.write(self.HEADER)

    def handle_slave_start(self, slave):
        """Handle slave start."""
        self._line = [str(slave)]

    def handle_store_start(self, store):
        """Handle store start."""
        self._line.append(self.STORE_NAMES[store])

    def handle_store_values(self, values):
        """Handle store values."""
        self.file_handle.writelines(self.handle_store_value(values))

    def handle_store_end(self, store):
        """Handle store end."""
        self._line.pop()

    def handle_store_value(self, values):
        """Handle store value."""
        for val_a, val_v in values:
            yield ",".join(self._line + [str(val_a), str(val_v)]) + self.NEWLINE


class XmlDatastoreSaver(ModbusDatastoreSaver):
    """An implementation of the modbus datastore saver.

    that persists the context as a XML document.
    """

    _context = None
    _store = None

    STORE_NAMES = {
        "i": "input-registers",
        "d": "discretes",
        "h": "holding-registers",
        "c": "coils",
    }

    def handle_save_start(self):
        """Handle save start."""
        self._context = xml.Element("context")
        self._root = xml.ElementTree(  # pylint: disable=attribute-defined-outside-init
            self._context
        )

    def handle_slave_start(self, slave):
        """Handle slave start."""
        self._slave = xml.SubElement(  # pylint: disable=attribute-defined-outside-init
            self._context, "slave"
        )
        self._slave.set("id", str(slave))

    def handle_store_start(self, store):
        """Handle store start."""
        self._store = xml.SubElement(self._slave, "store")
        self._store.set("function", self.STORE_NAMES[store])

    def handle_store_values(self, values):
        """Handle store values."""
        for address, value in values:
            entry = xml.SubElement(self._store, "entry")
            entry.text = str(value)
            entry.set("address", str(address))

    def handle_save_end(self):
        """Handle save end."""
        self._root.write(self.file_handle)
