#!/usr/bin/env python
"""
Note that this is not finished
"""
# --------------------------------------------------------------------------- #
# System
# --------------------------------------------------------------------------- #
import os
import getpass
import pickle
from threading import Thread

# --------------------------------------------------------------------------- #
# For Gui
# --------------------------------------------------------------------------- #
from Tkinter import *
from tkFileDialog import askopenfilename as OpenFilename
from twisted.internet import tksupport
root = Tk()
tksupport.install(root)

# --------------------------------------------------------------------------- #
# SNMP Simulator
# --------------------------------------------------------------------------- #
from twisted.internet import reactor
from twisted.internet import error as twisted_error
from pymodbus.server.async import ModbusServerFactory
from pymodbus.datastore import ModbusServerContext,ModbusSlaveContext

#--------------------------------------------------------------------------#
# Logging
#--------------------------------------------------------------------------#
import logging
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Application Error
# --------------------------------------------------------------------------- #
class ConfigurationException(Exception):
    """ Exception for configuration error """
    pass

# --------------------------------------------------------------------------- #
# Extra Global Functions
# --------------------------------------------------------------------------- #
# These are extra helper functions that don't belong in a class
# --------------------------------------------------------------------------- #
def root_test():
    """ Simple test to see if we are running as root """
    return getpass.getuser() == "root"

# --------------------------------------------------------------------------- #
# Simulator Class
# --------------------------------------------------------------------------- #
class Simulator(object):
    """
    Class used to parse configuration file and create and modbus
    datastore.

    The format of the configuration file is actually just a
    python pickle, which is a compressed memory dump from
    the scraper.
    """

    def __init__(self, config):
        """
        Trys to load a configuration file, lets the file not
        found exception fall through

        @param config The pickled datastore
        """
        try:
            self.file = open(config, "r")
        except Exception:
            raise ConfigurationException("File not found %s" % config)

    def _parse(self):
        """ Parses the config file and creates a server context """
        try:
            handle = pickle.load(self.file)
            dsd = handle['di']
            csd = handle['ci']
            hsd = handle['hr']
            isd = handle['ir']
        except KeyError:
            raise ConfigurationException("Invalid Configuration")
        slave = ModbusSlaveContext(d=dsd, c=csd, h=hsd, i=isd)
        return ModbusServerContext(slaves=slave)

    def _simulator(self):
        """ Starts the snmp simulator """
        ports = [502]+range(20000,25000)
        for port in ports:
            try:
                reactor.listenTCP(port, ModbusServerFactory(self._parse()))
                log.info('listening on port %d' % port)
                return port
            except twisted_error.CannotListenError:
                pass

    def run(self):
        """ Used to run the simulator """
        reactor.callWhenRunning(self._simulator)

# --------------------------------------------------------------------------- #
# Network reset thread
# --------------------------------------------------------------------------- #
# This is linux only, maybe I should make a base class that can be filled
# in for linux(debian/redhat)/windows/nix
# --------------------------------------------------------------------------- #
class NetworkReset(Thread):
    """
    This class is simply a daemon that is spun off at the end of the
    program to call the network restart function (an easy way to
    remove all the virtual interfaces)
    """
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        """ Run the network reset """
        os.system("/etc/init.d/networking restart")

# --------------------------------------------------------------------------- #
# Main Gui Class
# --------------------------------------------------------------------------- #
class SimulatorFrame(Frame):
    """
    This class implements the GUI for the flasher application
    """
    subnet  = 205
    number  = 1
    restart = 0

    def __init__(self, master, font):
        """ Sets up the gui, callback, and widget handles """
        Frame.__init__(self, master)
        self._widgets = []

        # --------------------------------------------------------------------------- #
        # Initialize Buttons Handles
        # --------------------------------------------------------------------------- #
        frame = Frame(self)
        frame.pack(side=BOTTOM, pady=5)

        button = Button(frame, text="Apply", command=self.start_clicked, font=font)
        button.pack(side=LEFT, padx=15)
        self._widgets.append(button)

        button = Button(frame, text="Help",  command=self.help_clicked, font=font)
        button.pack(side=LEFT, padx=15)
        self._widgets.append(button)

        button = Button(frame, text="Close", command=self.close_clicked, font=font)
        button.pack(side=LEFT, padx=15)
        #self._widgets.append(button) # we don't want to grey this out

        # --------------------------------------------------------------------------- #
        # Initialize Input Fields
        # --------------------------------------------------------------------------- #
        frame = Frame(self)
        frame.pack(side=TOP, padx=10, pady=5)

        self.tsubnet_value = StringVar()
        label = Label(frame, text="Starting Address", font=font)
        label.grid(row=0, column=0, pady=10)
        entry = Entry(frame, textvariable=self.tsubnet_value, font=font)
        entry.grid(row=0, column=1, pady=10)
        self._widgets.append(entry)

        self.tdevice_value = StringVar()
        label = Label(frame, text="Device to Simulate", font=font)
        label.grid(row=1, column=0, pady=10)
        entry = Entry(frame, textvariable=self.tdevice_value, font=font)
        entry.grid(row=1, column=1, pady=10)
        self._widgets.append(entry)

        image = PhotoImage(file='fileopen.gif')
        button = Button(frame, image=image, command=self.file_clicked)
        button.image = image
        button.grid(row=1, column=2, pady=10)
        self._widgets.append(button)

        self.tnumber_value = StringVar()
        label = Label(frame, text="Number of Devices", font=font)
        label.grid(row=2, column=0, pady=10)
        entry = Entry(frame, textvariable=self.tnumber_value, font=font)
        entry.grid(row=2, column=1, pady=10)
        self._widgets.append(entry)

        #if not root_test():
        #    self.error_dialog("This program must be run with root permissions!", True)

# --------------------------------------------------------------------------- #
# Gui helpers
# --------------------------------------------------------------------------- #
# Not callbacks, but used by them
# --------------------------------------------------------------------------- #
    def show_buttons(self, state=False):
        """ Greys out the buttons """
        state = 'active' if state else 'disabled'
        for widget in self._widgets:
            widget.configure(state=state)

    def destroy_interfaces(self):
        """ This is used to reset the virtual interfaces """
        if self.restart:
            n = NetworkReset()
            n.start()

    def error_dialog(self, message, quit=False):
        """ Quick pop-up for error messages """
        dialog = gtk.MessageDialog(
            parent          = self.window,
            flags           = gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
            type            = gtk.MESSAGE_ERROR,
            buttons         = gtk.BUTTONS_CLOSE,
            message_format  = message)
        dialog.set_title('Error')
        if quit:
            dialog.connect("response", lambda w, r: gtk.main_quit())
        else: dialog.connect("response", lambda w, r: w.destroy())
        dialog.show()

# --------------------------------------------------------------------------- #
# Button Actions
# --------------------------------------------------------------------------- #
# These are all callbacks for the various buttons
# --------------------------------------------------------------------------- #
    def start_clicked(self):
        """ Starts the simulator """
        start = 1
        base = "172.16"

        # check starting network
        net = self.tsubnet_value.get()
        octets = net.split('.')
        if len(octets) == 4:
            base = "%s.%s" % (octets[0], octets[1])
            net = int(octets[2]) % 255
            start = int(octets[3]) % 255
        else:
            self.error_dialog("Invalid starting address!");
            return False

        # check interface size
        size = int(self.tnumber_value.get())
        if (size >= 1):
            for i in range(start, (size + start)):
                j = i % 255
                cmd = "/sbin/ifconfig eth0:%d %s.%d.%d" % (i, base, net, j)
                os.system(cmd)
                if j == 254: net = net + 1
            self.restart = 1
        else:
            self.error_dialog("Invalid number of devices!");
            return False

        # check input file
        filename = self.tdevice_value.get()
        if os.path.exists(filename):
            self.show_buttons(state=False)
            try:
                handle = Simulator(config=filename)
                handle.run()
            except ConfigurationException as ex:
                self.error_dialog("Error %s" % ex)
                self.show_buttons(state=True)
        else:
            self.error_dialog("Device to emulate does not exist!");
            return False

    def help_clicked(self):
        """ Quick pop-up for about page """
        data = gtk.AboutDialog()
        data.set_version("0.1")
        data.set_name(('Modbus Simulator'))
        data.set_authors(["Galen Collins"])
        data.set_comments(('First Select a device to simulate,\n'
            + 'then select the starting subnet of the new devices\n'
            + 'then select the number of device to simulate and click start'))
        data.set_website("http://code.google.com/p/pymodbus/")
        data.connect("response", lambda w,r: w.hide())
        data.run()

    def close_clicked(self):
        """ Callback for close button """
        #self.destroy_interfaces()
        reactor.stop()

    def file_clicked(self):
        """ Callback for the filename change """
        file = OpenFilename()
        self.tdevice_value.set(file)

class SimulatorApp(object):
    """ The main wx application handle for our simulator
    """

    def __init__(self, master):
        """
        Called by wxWindows to initialize our application

        :param master: The master window to connect to
        """
        font  = ('Helvetica', 12, 'normal')
        frame = SimulatorFrame(master, font)
        frame.pack()

# --------------------------------------------------------------------------- #
# Main handle function
# --------------------------------------------------------------------------- #
# This is called when the application is run from a console
# We simply start the gui and start the twisted event loop
# --------------------------------------------------------------------------- #
def main():
    """
    Main control function
    This either launches the gui or runs the command line application
    """
    debug = True
    if debug:
        try:
            log.setLevel(logging.DEBUG)
    	    logging.basicConfig()
        except Exception as e:
    	    print("Logging is not supported on this system")
    simulator = SimulatorApp(root)
    root.title("Modbus Simulator")
    reactor.run()

# --------------------------------------------------------------------------- #
# Library/Console Test
# --------------------------------------------------------------------------- #
# If this is called from console, we start main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
