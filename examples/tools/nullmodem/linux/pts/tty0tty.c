/* ########################################################################

   tty0tty - linux null modem emulator 

   ########################################################################

   Copyright (c) : 2010  Luis Claudio Gambôa Lopes

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2, or (at your option)
   any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

   For e-mail suggestions :  lcgamboa@yahoo.com
   ######################################################################## */


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>

#include <termio.h>

int
ptym_open(char *pts_name, char *pts_name_s , int pts_namesz)
{
    char    *ptr;
    int     fdm;

    strncpy(pts_name, "/dev/ptmx", pts_namesz);
    pts_name[pts_namesz - 1] = '\0';

    fdm = posix_openpt(O_RDWR | O_NONBLOCK);
    if (fdm < 0)
        return(-1);
    if (grantpt(fdm) < 0) 
    {
        close(fdm);
        return(-2);
    }
    if (unlockpt(fdm) < 0) 
    {
        close(fdm);
        return(-3);
    }
    if ((ptr = ptsname(fdm)) == NULL) 
    {
        close(fdm);
        return(-4);
    }
    
    strncpy(pts_name_s, ptr, pts_namesz);
    pts_name[pts_namesz - 1] = '\0';

    return(fdm);        
}


int
conf_ser(int serialDev)
{

int rc=0;
struct termios params;

// Get terminal atributes
rc = tcgetattr(serialDev, &params);

// Modify terminal attributes
cfmakeraw(&params);

rc = cfsetispeed(&params, B9600);

rc = cfsetospeed(&params, B9600);

// CREAD - Enable port to read data
// CLOCAL - Ignore modem control lines
params.c_cflag |= (B9600 |CS8 | CLOCAL | CREAD);

// Make Read Blocking
//fcntl(serialDev, F_SETFL, 0);

// Set serial attributes
rc = tcsetattr(serialDev, TCSANOW, &params);

// Flush serial device of both non-transmitted
// output data and non-read input data....
tcflush(serialDev, TCIOFLUSH);


  return EXIT_SUCCESS;
}


int main(void)
{
  char master1[1024];
  char slave1[1024];
  char master2[1024];
  char slave2[1024];

  int fd1;
  int fd2;

  char c1,c2;

  fd1=ptym_open(master1,slave1,1024);

  fd2=ptym_open(master2,slave2,1024);

   printf("(%s) <=> (%s)\n",slave1,slave2);


   conf_ser(fd1);
   conf_ser(fd2);


  while(1)
  {
    if(read (fd1,&c1,1) == 1) write(fd2,&c1,1);
    usleep(20);
    if(read (fd2,&c2,1) == 1) write(fd1,&c2,1);
    usleep(20);
  };

  close(fd1);
  close(fd2);

  return EXIT_SUCCESS;
}
