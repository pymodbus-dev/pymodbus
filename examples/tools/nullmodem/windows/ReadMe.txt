                 =============================
                 Null-modem emulator (com0com)
                 =============================

INTRODUCTION
============

The Null-modem emulator is an open source kernel-mode virtual serial
port driver for Windows, available freely under GPL license.
You can create an unlimited number of virtual COM port
pairs and use any pair to connect one application to another.
Each COM port pair provides two COM ports with default names starting
at CNCA0 and CNCB0. The output to one port is the input from other
port and vice versa.

Usually one port of the pair is used by Windows application that
requires a COM port to communicate with a device and other port is
used by device emulation program.

For example, to send/receive faxes over IP you can connect Windows Fax
application to CNCA0 port and t38modem (http://t38modem.sourceforge.net/)
to CNCB0 port. In this case the t38modem is a fax modem emulation program.

In conjunction with the hub4com the com0com allows you to
  - handle data and signals from a single real serial device by a number of
    different applications. For example, several applications can share data
    from one GPS device;
  - use real serial ports of remote computer like if they exist on the local
    computer (supports RFC 2217).

The homepage for com0com project is http://com0com.sourceforge.net/.


INSTALLING
==========

NOTE (Windows Vista/Windows Server 2008/Windows 7):
  Before installing/uninstalling the com0com driver or adding/removing/changing
  ports the User Account Control (UAC) should be turned off (require reboot).

NOTE (x64-based Windows Vista/Windows Server 2008/Windows 7):
  The com0com.sys is a test-signed kernel-mode driver that will not load by
  default. To enable test signing, enter command:

    bcdedit.exe -set TESTSIGNING ON

  and reboot the computer.

NOTE:
  Turning off UAC or enabling test signing will impair computer security.

Simply run the installer (setup.exe). An installation wizard will guide
you through the required steps.
If the Found New Hardware Wizard will pop up then
  - select "No, not this time" and click Next;
  - select "Install the software automatically (Recommended)" and click Next.
The one COM port pair with names CNCA0 and CNCB0 will be available on your
system after the installation.

You can add more pairs with the Setup Command Prompt:

  1. Launch the Setup Command Prompt shortcut.
  2. Enter the install command, for example:

       command> install - -

The system will create 3 new virtual devices. One of the devices has
name "com0com - bus for serial port pair emulator" and other two of
them have name "com0com - serial port emulator" and located on CNCAn
and CNCBn ports.

To get more info enter the help command, for example:

       command> help

Alternatively to setup ports you can invoke GUI-based setup utility by
launching Setup shortcut (Microsoft .NET Framework 2.0 is required).

TESTING
=======

  1. Start the HyperTerminal on CNCA0 port.
  2. Start the HyperTerminal on CNCB0 port.
  3. The output to CNCA0 port should be the input from CNCB0 port and
     vice versa.


UNINSTALLING
============

Simply launch the com0com's Uninstall shortcut in the Start Menu or remove
the "Null-modem emulator (com0com)" entry from the "Add/Remove Programs"
section in the Control Panel. An uninstallation wizard will guide
you through the required steps.

HINT: To uninstall the old version of com0com (distributed w/o installer)
install the new one and then uninstall it.


FAQs & HOWTOs
=============

Q. Is it possible to run com0com on Windows 9x platform?
A. No, it is not possible. You need Windows 2000 platform or newer.

Q. Is it possible to install or uninstall com0com silently (with no user
   intervention and no user interface)?
A. Yes, it's possible with /S option, for example:

     setup.exe /S
     "%ProgramFiles%\com0com\uninstall.exe" /S

   You can specify the installation directory with /D option, for example:

     setup.exe /S /D=C:\Program Files\com0com

   NOTE: Silent installation of com0com will not install any port pairs.

Q. Is it possible to change the names CNCA0 and CNCB0 to COM2 and COM3?
A. Yes, it's possible. To change the names:

   1. Launch the Setup Command Prompt shortcut.
   2. Enter the change commands, for example:

      command> change CNCA0 PortName=COM2
      command> change CNCB0 PortName=COM3

Q. The baud rate setting does not seem to make a difference: data is always
   transferred at the same speed. How to enable the baud rate emulation?
A. To enable baud rate emulation for transferring data from CNCA0 to CNCB0:

   1. Launch the Setup Command Prompt shortcut.
   2. Enter the change command, for example:

      command> change CNCA0 EmuBR=yes

Q. The HyperTerminal test succeeds, but I get a failure when trying to open the
   port with CreateFile("CNCA0", ...). GetLastError() returns ERROR_FILE_NOT_FOUND.
A. You must prefix the port name with the special characters "\\.\". Try to open
   the port with CreateFile("\\\\.\\CNCA0", ...).

Q. My application hangs during its startup when it sends anything to one paired
   COM port. The only way to unhang it is to start HyperTerminal, which is connected
   to the other paired COM port. I didn't have this problem with physical serial
   ports.
A. Your application can hang because receive buffer overrun is disabled by
   default. You can fix the problem by enabling receive buffer overrun for the
   receiving port. Also, to prevent some flow control issues you need to enable
   baud rate emulation for the sending port. So, if your application use port CNCA0
   and other paired port is CNCB0, then:

   1. Launch the Setup Command Prompt shortcut.
   2. Enter the change commands, for example:

      command> change CNCB0 EmuOverrun=yes
      command> change CNCA0 EmuBR=yes

Q. I have to write an application connected to one side of the com0com port pair,
   and I don't want users to 'see' all the virtual ports created by com0com, but
   only the really available ones.
A. if your application use port CNCB0 and other (used by users) paired port is CNCA0,
   then CNCB0 can be 'hidden' and CNCA0 can be 'shown' on opening CNCB0 by your
   application. To enable it:

   1. Launch the Setup Command Prompt shortcut.
   2. Enter the change commands:

      command> change CNCB0 ExclusiveMode=yes
      command> change CNCA0 PlugInMode=yes

Q. When I add a port pair, why does Windows XP always pops up a Found New Hardware
   Wizard? The drivers are already there and it can install them silently in the
   background and report when the device is ready.
A. It's because there is not signed com0com.cat catalog file. It can be created on
   your test computer by this way:

   1. Create a catalog file, for example:

      cd "C:\Program Files\com0com"
      inf2cat /driver:. /os:XP_X86

   2. Create a test certificate, for example:

      makecert -r -n "CN=com0com (test)" -sv com0com.pvk com0com.cer
      pvk2pfx -pvk com0com.pvk -spc com0com.cer -pfx com0com.pfx

   3. Sign the catalog file by test certificate, for example:

      signtool sign /v /f com0com.pfx com0com.cat

   4. Install a test certificate to the Trusted Root Certification Authorities
      certificate store and the Trusted Publishers certificate store, for example:

      certmgr -add com0com.cer -s -r localMachine root
      certmgr -add com0com.cer -s -r localMachine trustedpublisher

   The inf2cat tool can be installed with the Winqual Submission Tool.
   The makecert, pvk2pfx, signtool and certmgr tools can be installed with the
   Platform Software Development Kit (SDK).

Q. How to monitor and get the paired port settings (baud rate, byte size, parity
   and stop bits)?
A. It can be done with extended IOCTL_SERIAL_LSRMST_INSERT. See example in

   http://com0com.sourceforge.net/examples/LSRMST_INSERT/tstser.cpp

Q. To transfer state to CTS and DSR they wired to RTS and DTR. How to transfer
   state to DCD and RING?
A. The OUT1 can be wired to DCD and OUT2 to RING. Use extended
   IOCTL_SERIAL_SET_MODEM_CONTROL and IOCTL_SERIAL_GET_MODEM_CONTROL to change
   state of OUT1 and OUT2.  See example in

   http://com0com.sourceforge.net/examples/MODEM_CONTROL/tstser.cpp

Q. What version am I running?
A. In the device manager, the driver properties page shows the version and date
   of the com0com.inf file, while the driver details page shows a version of
   com0com.sys file. The version of com0com.sys file is the version that you
   are running.

Q. I'm able to use some application to talk to some hardware using com2tcp when
   both the com2tcp 'server' and 'client' are running on the same computer.
   When I try to move the client to a remote computer the application gives me
   a timeout message and has no settings to increase the timeout. How to fix
   the problem?
A. Try to ajust AddRTTO and AddRITO params for application's COM port:

   1. Launch the Setup Command Prompt shortcut.
   2. Enter the change command, for example:

      command> change CNCA0 AddRTTO=100,AddRITO=100

Q. I would like to be able to add, remove and rename virtual comm ports from my
   own custom application. Is there an API that I can use or some command line
   utility that will do the job?
A. The setupc.exe is a command line utility that will do the job. To get more
   info enter:

      setupc help

   BTW: The setupg.exe is a GUI wrapper for setupc.exe.

Q. I need to use com0com ports with an application that doesn't recognize
   com0com ports as "real" com ports. It does not see a com0com port even
   though I have changed it's name to COMx. Is there a com0com settings that
   will make the port appear to be a "real" com port?
A. No, there is not, but you can "deceive" the application this way:

   1. With the "Add/Remove Hardware" wizard install new standard serial port.
      You don't need a real serial hardware to do it. Select non conflicted
      IO/IRQ resources.
   2. With the "Device Manager" disable the newly created port (let it be
      COM4).
   3. Launch the Setup Command Prompt shortcut.
   4. Install the pair of ports, were one of them has name COM4, for example:

      command> install PortName=COM4 -

      Ignore a warning about the COM4 is "in use" (press Continue).

Q. Is it possible to configure the com0com to randomly corrupt the data? It
   would be nice to have this feature so that we can test our application
   robustness.
A. Yes, it's possible by setting EmuNoise parameter:

   1. Launch the Setup Command Prompt shortcut.
   2. Enter the change command, for example:

      command> change CNCA0 EmuNoise=0.00001,EmuBR=yes,EmuOverrun=yes
      command> change CNCB0 EmuNoise=0.00001,EmuBR=yes,EmuOverrun=yes

   Now each character frame (including idle frames) will be corrupted with
   probability 0.00001.

Q. What is the maximum number of port pairs that can be defined?
A. It depends from your system. The com0com itself has internal limit
   1000000 port pairs.

Q. In my application, users could be installing up to 250 com port pairs.
   Initially, the installation is fairly quick, but each additional com port
   generally takes longer to install than the previous one. It quickly
   becomes unacceptable for a user to be expected to wait for the installation.
A. It's because the installing of each next port pair requires to update driver
   for all installed pairs. You can speed up installing of multiple com port
   pairs by using install commands with --no-update option and finish them by
   update command, for example:

      command> --no-update install - -
      command> --no-update install - -
      ...
      command> --no-update install - -
      command> update

   Another example:

      > cd /D "%ProgramFiles%\com0com"
      > FOR /L %i IN (0,1,249) DO setupc --no-update install - -
      > setupc update

Q. I am using the 64-bit version of com0com and I am having trouble. I'd like
   to debug this, but I can not find any free serial port monitor software,
   like portmon that works with a 64-bit OS. Does anyone know of any?
A. You can try to use internal com0com's tracing for debuging:

      - get trace.reg file from com0com's source;
      - import trace.reg to the Registry;
      - reload driver (or reboot system);
      - do your tests and watch results in C:\com0com.log file.

   To disable tracing reinstall com0com or import trace_disable.reg to the
   Registry and reload driver.
