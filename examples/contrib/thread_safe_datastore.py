# pylint: disable=missing-type-doc
"""Thread safe datastore."""
import threading
from contextlib import contextmanager

from pymodbus.datastore.store import BaseModbusDataBlock


class ContextWrapper:
    """This is a simple wrapper around enter and exit functions

    that conforms to the python context manager protocol:

    with ContextWrapper(enter, leave):
        do_something()
    """

    def __init__(self, enter=None, leave=None, factory=None):
        """Initialize."""
        self._enter = enter
        self._leave = leave
        self._factory = factory

    def __enter__(self):
        """Do on enter."""
        if self.enter:  # pylint: disable=no-member
            self._enter()
        return self if not self._factory else self._factory()

    def __exit__(self, *args):
        """Do on exit."""
        if self._leave:
            self._leave()


class ReadWriteLock:
    """This reader writer lock guarantees write order,

    but not read order and is generally biased towards allowing writes
    if they are available to prevent starvation.
    TODO:
    * allow user to choose between read/write/random biasing
    - currently write biased
    - read biased allow N readers in queue
    - random is 50/50 choice of next
    """

    def __init__(self):
        """Initialize a new instance of the ReadWriteLock"""
        self.queue = []  # the current writer queue
        self.lock = threading.Lock()  # the underlying condition lock
        self.read_condition = threading.Condition(
            self.lock
        )  # the single reader condition
        self.readers = 0  # the number of current readers
        self.writer = False  # is there a current writer

    def __is_pending_writer(self):
        """Check is pending writer."""
        return self.writer or (  # if there is a current writer
            self.queue  # or if there is a waiting writer
            and (self.queue[0] != self.read_condition)
        )

    def acquire_reader(self):
        """Notify the lock that a new reader is requesting the underlying resource."""
        with self.lock:
            if self.__is_pending_writer():  # if there are existing writers waiting
                if (
                    self.read_condition not in self.queue
                ):  # do not pollute the queue with readers
                    self.queue.append(
                        self.read_condition
                    )  # add the readers in line for the queue
                while (
                    self.__is_pending_writer()
                ):  # until the current writer is finished
                    self.read_condition.wait(1)  # wait on our condition
                if self.queue and self.read_condition == self.queue[0]:
                    self.queue.pop(0)  # then go ahead and remove it
            self.readers += 1  # update the current number of readers

    def acquire_writer(self):
        """Notify the lock that a new writer is requesting the underlying resource."""
        with self.lock:
            if self.writer or self.readers:
                condition = threading.Condition(self.lock)
                # create a condition just for this writer
                self.queue.append(condition)  # and put it on the waiting queue
                while self.writer or self.readers:  # until the write lock is free
                    condition.wait(1)
                self.queue.pop(0)
            self.writer = True  # stop other writers from operating

    def release_reader(self):
        """Notify the lock that an existing reader is finished with the underlying resource."""
        with self.lock:
            self.readers = max(0, self.readers - 1)  # readers should never go below 0
            if not self.readers and self.queue:  # if there are no active readers
                self.queue[0].notify_all()  # then notify any waiting writers

    def release_writer(self):
        """Notify the lock that an existing writer is finished with the underlying resource."""
        with self.lock:
            self.writer = False  # give up current writing handle
            if self.queue:  # if someone is waiting in the queue
                self.queue[0].notify_all()  # wake them up first
            else:
                self.read_condition.notify_all()  # otherwise wake up all possible readers

    @contextmanager
    def get_reader_lock(self):
        """Wrap some code with a reader lock using the python context manager protocol::

        with rwlock.get_reader_lock():
            do_read_operation()
        """
        try:
            self.acquire_reader()
            yield self
        finally:
            self.release_reader()

    @contextmanager
    def get_writer_lock(self):
        """Wrap some code with a writer lock using the python context manager protocol::

        with rwlock.get_writer_lock():
            do_read_operation()
        """
        try:
            self.acquire_writer()
            yield self
        finally:
            self.release_writer()


class ThreadSafeDataBlock(BaseModbusDataBlock):
    """This is a simple decorator for a data block.

    This allows a user to inject an existing data block which can then be
    safely operated on from multiple cocurrent threads.

    It should be noted that the choice was made to lock around the
    datablock instead of the manager as there is less source of
    contention (writes can occur to slave 0x01 while reads can
    occur to slave 0x02).
    """

    def __init__(self, block):
        """Initialize a new thread safe decorator

        :param block: The block to decorate
        """
        self.rwlock = ReadWriteLock()
        self.block = block

    def validate(self, address, count=1):
        """Check to see if the request is in range

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        """
        with self.rwlock.get_reader_lock():
            return self.block.validate(address, count)

    def getValues(self, address, count=1):
        """Return the requested values of the datastore

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        with self.rwlock.get_reader_lock():
            return self.block.getValues(address, count)

    def setValues(self, address, values):
        """Set the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        """
        with self.rwlock.get_writer_lock():
            return self.block.setValues(address, values)


if __name__ == "__main__":  # pylint: disable=too-complex

    class AtomicCounter:
        """Atomic counter."""

        def __init__(self, **kwargs):
            """Init."""
            self.counter = kwargs.get("start", 0)
            self.finish = kwargs.get("finish", 1000)
            self.lock = threading.Lock()

        def increment(self, count=1):
            """Increment."""
            with self.lock:
                self.counter += count

        def is_running(self):
            """Is running."""
            return self.counter <= self.finish

    locker = ReadWriteLock()
    readers, writers = AtomicCounter(), AtomicCounter()

    def read():
        """Read."""
        while writers.is_running() and readers.is_running():
            with locker.get_reader_lock():
                readers.increment()

    def write():
        """Write."""
        while writers.is_running() and readers.is_running():
            with locker.get_writer_lock():
                writers.increment()

    rthreads = [threading.Thread(target=read) for i in range(50)]
    wthreads = [threading.Thread(target=write) for i in range(2)]
    for t in rthreads + wthreads:
        t.start()
    for t in rthreads + wthreads:
        t.join()
    print(f"readers[{readers.counter}] writers[{writers.counter}]")
