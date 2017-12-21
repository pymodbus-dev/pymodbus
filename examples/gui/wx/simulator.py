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
import wx
from twisted.internet import wxreactor
wxreactor.install()

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
                print 'listening on port', port
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
        """ Initializes a new instance of the network reset thread """
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        """ Run the network reset """
        os.system("/etc/init.d/networking restart")

# --------------------------------------------------------------------------- #
# Main Gui Class
# --------------------------------------------------------------------------- #
class SimulatorFrame(wx.Frame):
    """
    This class implements the GUI for the flasher application
    """
    subnet = 205
    number = 1
    restart = 0

    def __init__(self, parent, id, title):
        """
        Sets up the gui, callback, and widget handles
        """
        wx.Frame.__init__(self, parent, id, title)
        wx.EVT_CLOSE(self, self.close_clicked)

        # --------------------------------------------------------------------------- #
        # Add button row
        # --------------------------------------------------------------------------- #
        panel = wx.Panel(self, -1)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.Button(panel, 1, 'Apply'), 1)
        box.Add(wx.Button(panel, 2, 'Help'),  1)
        box.Add(wx.Button(panel, 3, 'Close'), 1)
        panel.SetSizer(box)

        # --------------------------------------------------------------------------- #
        # Add input boxes
        # --------------------------------------------------------------------------- #
        #self.tdevice    = self.tree.get_widget("fileTxt")
        #self.tsubnet    = self.tree.get_widget("addressTxt")
        #self.tnumber    = self.tree.get_widget("deviceTxt")

        # --------------------------------------------------------------------------- #
        # Tie callbacks
        # --------------------------------------------------------------------------- #
        self.Bind(wx.EVT_BUTTON, self.start_clicked, id=1)
        self.Bind(wx.EVT_BUTTON, self.help_clicked,  id=2)
        self.Bind(wx.EVT_BUTTON, self.close_clicked, id=3)

        #if not root_test():
        #    self.error_dialog("This program must be run with root permissions!", True)

# --------------------------------------------------------------------------- #
# Gui helpers
# --------------------------------------------------------------------------- #
# Not callbacks, but used by them
# --------------------------------------------------------------------------- #
    def show_buttons(self, state=False, all=0):
        """ Greys out the buttons """
        if all:
            self.window.set_sensitive(state)
        self.bstart.set_sensitive(state)
        self.tdevice.set_sensitive(state)
        self.tsubnet.set_sensitive(state)
        self.tnumber.set_sensitive(state)

    def destroy_interfaces(self):
        """ This is used to reset the virtual interfaces """
        if self.restart:
            n = NetworkReset()
            n.start()

    def error_dialog(self, message, quit=False):
        """ Quick pop-up for error messages """
        log.debug("error event called")
        dialog = wx.MessageDialog(self, message, 'Error',
            wx.OK | wx.ICON_ERROR)
        dialog.ShowModel()
        if quit: self.Destroy()
        dialog.Destroy()

# --------------------------------------------------------------------------- #
# Button Actions
# --------------------------------------------------------------------------- #
# These are all callbacks for the various buttons
# --------------------------------------------------------------------------- #
    def start_clicked(self, widget):
        """ Starts the simulator """
        start = 1
        base = "172.16"

        # check starting network
        net = self.tsubnet.get_text()
        octets = net.split('.')
        if len(octets) == 4:
            base = "%s.%s" % (octets[0], octets[1])
            net = int(octets[2]) % 255
            start = int(octets[3]) % 255
        else:
            self.error_dialog("Invalid starting address!");
            return False

        # check interface size
        size = int(self.tnumber.get_text())
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
        if os.path.exists(self.file):
            self.show_buttons(state=False)
            try:
                handle = Simulator(config=self.file)
                handle.run()
            except ConfigurationException, ex:
                self.error_dialog("Error %s" % ex)
                self.show_buttons(state=True)
        else:
            self.error_dialog("Device to emulate does not exist!");
            return False

    def help_clicked(self, widget):
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

    def close_clicked(self, event):
        """ Callback for close button """
        log.debug("close event called")
        reactor.stop()

    def file_changed(self, event):
        """ Callback for the filename change """
        self.file = widget.get_filename()

class SimulatorApp(wx.App):
    """ The main wx application handle for our simulator
    """

    def OnInit(self):
        """ Called by wxWindows to initialize our application

        :returns: Always True
        """
        log.debug("application initialize event called")
        reactor.registerWxApp(self)
        frame = SimulatorFrame(None, -1, "Pymodbus Simulator")
        frame.CenterOnScreen()
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

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
        except Exception, e:
    	    print "Logging is not supported on this system"
    simulator = SimulatorApp(0)
    reactor.run()

# --------------------------------------------------------------------------- #
# Library/Console Test
# --------------------------------------------------------------------------- #
# If this is called from console, we start main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
