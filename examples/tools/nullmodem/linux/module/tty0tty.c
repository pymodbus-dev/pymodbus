/* ########################################################################

   tty0tty - linux null modem emulator (module) 

   ########################################################################

   Copyright (c) : 2010  Luis Claudio Gambôa Lopes
 
    Based in Tiny TTY driver -  Copyright (C) 2002-2004 Greg Kroah-Hartman (greg@kroah.com)

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

#include <linux/kernel.h>
#include <linux/errno.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/wait.h>
#include <linux/tty.h>
#include <linux/tty_driver.h>
#include <linux/tty_flip.h>
#include <linux/serial.h>
#include <linux/sched.h>
#include <asm/uaccess.h>


#define DRIVER_VERSION "v1.0"
#define DRIVER_AUTHOR "Luis Claudio Gamboa Lopes <lcgamboa@yahoo.com>"
#define DRIVER_DESC "tty0tty null modem driver"

/* Module information */
MODULE_AUTHOR( DRIVER_AUTHOR );
MODULE_DESCRIPTION( DRIVER_DESC );
MODULE_LICENSE("GPL");


#define TINY_TTY_MAJOR		240	/* experimental range */
#define TINY_TTY_MINORS		8	/* device number, always even*/

/* fake UART values */
//out
#define MCR_DTR		0x01
#define MCR_RTS		0x02
#define MCR_LOOP	0x04
//in
#define MSR_CTS		0x10
#define MSR_CD		0x20
#define MSR_DSR		0x40
#define MSR_RI		0x80

struct tty0tty_serial {
	struct tty_struct	*tty;		/* pointer to the tty for this device */
	int			open_count;	/* number of times this port has been opened */
	struct semaphore	sem;		/* locks this structure */

	/* for tiocmget and tiocmset functions */
	int			msr;		/* MSR shadow */
	int			mcr;		/* MCR shadow */

	/* for ioctl fun */
	struct serial_struct	serial;
	wait_queue_head_t	wait;
	struct async_icount	icount;
};

static struct tty0tty_serial *tty0tty_table[TINY_TTY_MINORS];	/* initially all NULL */


static int tty0tty_open(struct tty_struct *tty, struct file *file)
{
	struct tty0tty_serial *tty0tty;
        int index;
	int msr=0;	
	int mcr=0;

#ifdef SCULL_DEBUG
	printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif	
        /* initialize the pointer in case something fails */
	tty->driver_data = NULL;

	/* get the serial object associated with this tty pointer */
	index = tty->index;
	tty0tty = tty0tty_table[index];
	if (tty0tty == NULL) {
		/* first time accessing this device, let's create it */
		tty0tty = kmalloc(sizeof(*tty0tty), GFP_KERNEL);
		if (!tty0tty)
			return -ENOMEM;

		sema_init(&tty0tty->sem, 1);
		tty0tty->open_count = 0;

		tty0tty_table[index] = tty0tty;
        
              }

         if( (index % 2) == 0)
         { 
                if(tty0tty_table[index+1] != NULL) 
	          if (tty0tty_table[index+1]->open_count > 0)
                    mcr=tty0tty_table[index+1]->mcr;
         }
         else
         {
                if(tty0tty_table[index-1] != NULL) 
	          if (tty0tty_table[index-1]->open_count > 0)
                    mcr=tty0tty_table[index-1]->mcr;
         } 
	
//null modem connection

         if( (mcr & MCR_RTS) == MCR_RTS )
         {
	        msr |= MSR_CTS;
         }
 
         if( (mcr & MCR_DTR) == MCR_DTR )
         {
	        msr |= MSR_DSR;
	        msr |= MSR_CD;
         }
	
	tty0tty->msr = msr;
 
	down(&tty0tty->sem);

	/* save our structure within the tty structure */
	tty->driver_data = tty0tty;
	tty0tty->tty = tty;

	++tty0tty->open_count;

	up(&tty0tty->sem);
	return 0;
}

static void do_close(struct tty0tty_serial *tty0tty)
{
	down(&tty0tty->sem);
#ifdef SCULL_DEBUG
	printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	if (!tty0tty->open_count) {
		/* port was never opened */
		goto exit;
	}

	--tty0tty->open_count;
exit:
	up(&tty0tty->sem);
    
   return;
}

static void tty0tty_close(struct tty_struct *tty, struct file *file)
{
	struct tty0tty_serial *tty0tty = tty->driver_data;
	
#ifdef SCULL_DEBUG
        printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	if (tty0tty)
		do_close(tty0tty);
}	

static int tty0tty_write(struct tty_struct *tty, const unsigned char *buffer, int count)
{
	struct tty0tty_serial *tty0tty = tty->driver_data;
	int retval = -EINVAL;
	struct tty_struct  *ttyx = NULL;	

        if (!tty0tty)
		return -ENODEV;

	down(&tty0tty->sem);

	if (!tty0tty->open_count)
		/* port was not opened */
		goto exit;

        if( (tty0tty->tty->index % 2) == 0)
        { 
         if(tty0tty_table[tty0tty->tty->index+1] != NULL) 
	   if (tty0tty_table[tty0tty->tty->index+1]->open_count > 0)
             ttyx=tty0tty_table[tty0tty->tty->index+1]->tty;
        }
        else
        {
         if(tty0tty_table[tty0tty->tty->index-1] != NULL) 
	   if (tty0tty_table[tty0tty->tty->index-1]->open_count > 0)
             ttyx=tty0tty_table[tty0tty->tty->index-1]->tty;
        } 

//        tty->low_latency=1;

        if(ttyx != NULL)
        {
          tty_insert_flip_string(ttyx, buffer, count);
          tty_flip_buffer_push(ttyx);
	  retval=count;
        } 
		
exit:
	up(&tty0tty->sem);
	return retval;
}

static int tty0tty_write_room(struct tty_struct *tty) 
{
	struct tty0tty_serial *tty0tty = tty->driver_data;
	int room = -EINVAL;
	
	if (!tty0tty)
		return -ENODEV;

	down(&tty0tty->sem);
	
	if (!tty0tty->open_count) {
		/* port was not opened */
		goto exit;
	}

	/* calculate how much room is left in the device */
	room = 255;

exit:
	up(&tty0tty->sem);
	return room;
}

#define RELEVANT_IFLAG(iflag) ((iflag) & (IGNBRK|BRKINT|IGNPAR|PARMRK|INPCK))

static void tty0tty_set_termios(struct tty_struct *tty, struct ktermios *old_termios)
{
	unsigned int cflag;
	
#ifdef SCULL_DEBUG
        printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	cflag = tty->termios->c_cflag;

	/* check that they really want us to change something */
	if (old_termios) {
		if ((cflag == old_termios->c_cflag) &&
		    (RELEVANT_IFLAG(tty->termios->c_iflag) == 
		     RELEVANT_IFLAG(old_termios->c_iflag))) {
#ifdef SCULL_DEBUG
			printk(KERN_DEBUG " - nothing to change...\n");
#endif
			return;
		}
	}

#ifdef SCULL_DEBUG
	/* get the byte size */
	switch (cflag & CSIZE) {
		case CS5:
			printk(KERN_DEBUG " - data bits = 5\n");
			break;
		case CS6:
			printk(KERN_DEBUG " - data bits = 6\n");
			break;
		case CS7:
			printk(KERN_DEBUG " - data bits = 7\n");
			break;
		default:
		case CS8:
			printk(KERN_DEBUG " - data bits = 8\n");
			break;
	}
	
	/* determine the parity */
	if (cflag & PARENB)
		if (cflag & PARODD)
			printk(KERN_DEBUG " - parity = odd\n");
		else
			printk(KERN_DEBUG " - parity = even\n");
	else
		printk(KERN_DEBUG " - parity = none\n");

	/* figure out the stop bits requested */
	if (cflag & CSTOPB)
		printk(KERN_DEBUG " - stop bits = 2\n");
	else
		printk(KERN_DEBUG " - stop bits = 1\n");

	/* figure out the hardware flow control settings */
	if (cflag & CRTSCTS)
		printk(KERN_DEBUG " - RTS/CTS is enabled\n");
	else
		printk(KERN_DEBUG " - RTS/CTS is disabled\n");
	
	/* determine software flow control */
	/* if we are implementing XON/XOFF, set the start and 
	 * stop character in the device */
	if (I_IXOFF(tty) || I_IXON(tty)) {
		unsigned char stop_char  = STOP_CHAR(tty);
		unsigned char start_char = START_CHAR(tty);

		/* if we are implementing INBOUND XON/XOFF */
		if (I_IXOFF(tty))
			printk(KERN_DEBUG " - INBOUND XON/XOFF is enabled, "
				"XON = %2x, XOFF = %2x\n", start_char, stop_char);
		else
			printk(KERN_DEBUG" - INBOUND XON/XOFF is disabled\n");

		/* if we are implementing OUTBOUND XON/XOFF */
		if (I_IXON(tty))
			printk(KERN_DEBUG" - OUTBOUND XON/XOFF is enabled, "
				"XON = %2x, XOFF = %2x\n", start_char, stop_char);
		else
			printk(KERN_DEBUG" - OUTBOUND XON/XOFF is disabled\n");
	}

	/* get the baud rate wanted */
	printk(KERN_DEBUG " - baud rate = %d\n", tty_get_baud_rate(tty));
#endif
}


static int tty0tty_tiocmget(struct tty_struct *tty, struct file *file)
{
	struct tty0tty_serial *tty0tty = tty->driver_data;

	unsigned int result = 0;
	unsigned int msr = tty0tty->msr;
	unsigned int mcr = tty0tty->mcr;
	

	result = ((mcr & MCR_DTR)  ? TIOCM_DTR  : 0) |	/* DTR is set */
             ((mcr & MCR_RTS)  ? TIOCM_RTS  : 0) |	/* RTS is set */
             ((mcr & MCR_LOOP) ? TIOCM_LOOP : 0) |	/* LOOP is set */
             ((msr & MSR_CTS)  ? TIOCM_CTS  : 0) |	/* CTS is set */
             ((msr & MSR_CD)   ? TIOCM_CAR  : 0) |	/* Carrier detect is set*/
             ((msr & MSR_RI)   ? TIOCM_RI   : 0) |	/* Ring Indicator is set */
             ((msr & MSR_DSR)  ? TIOCM_DSR  : 0);	/* DSR is set */

	return result;
}

static int tty0tty_tiocmset(struct tty_struct *tty, struct file *file,
                         unsigned int set, unsigned int clear)
{
	struct tty0tty_serial *tty0tty = tty->driver_data;
	unsigned int mcr = tty0tty->mcr;
	unsigned int msr=0;
        
#ifdef SCULL_DEBUG
        printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif

        if( (tty0tty->tty->index % 2) == 0)
        { 
           if(tty0tty_table[tty0tty->tty->index+1] != NULL) 
	     if (tty0tty_table[tty0tty->tty->index+1]->open_count > 0)
               msr=tty0tty_table[tty0tty->tty->index+1]->msr;
        }
        else
        {
           if(tty0tty_table[tty0tty->tty->index-1] != NULL) 
	     if (tty0tty_table[tty0tty->tty->index-1]->open_count > 0)
               msr=tty0tty_table[tty0tty->tty->index-1]->msr;
        } 
	
//null modem connection

	if (set & TIOCM_RTS)
        {  
	   mcr |= MCR_RTS;
	   msr |= MSR_CTS;
        }
 
	if (set & TIOCM_DTR)
        {
	   mcr |= MCR_DTR;
	   msr |= MSR_DSR;
	   msr |= MSR_CD;
        }

	if (clear & TIOCM_RTS)
        {
	   mcr &= ~MCR_RTS;
	   msr &= ~MSR_CTS;
        }
 
	if (clear & TIOCM_DTR)
        {
  	   mcr &= ~MCR_DTR;
	   msr &= ~MSR_DSR;
	   msr &= ~MSR_CD;
        }
        

	/* set the new MCR value in the device */
	tty0tty->mcr = mcr;
        
        if( (tty0tty->tty->index % 2) == 0)
        {  
           if(tty0tty_table[tty0tty->tty->index+1] != NULL) 
	     if (tty0tty_table[tty0tty->tty->index+1]->open_count > 0)
               tty0tty_table[tty0tty->tty->index+1]->msr=msr;
        }
        else
        {
           if(tty0tty_table[tty0tty->tty->index-1] != NULL) 
	     if (tty0tty_table[tty0tty->tty->index-1]->open_count > 0)
               tty0tty_table[tty0tty->tty->index-1]->msr=msr;
        } 
	return 0;
}


static int tty0tty_ioctl_tiocgserial(struct tty_struct *tty, struct file *file,
                      unsigned int cmd, unsigned long arg)
{
	struct tty0tty_serial *tty0tty = tty->driver_data;
	
#ifdef SCULL_DEBUG
        printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	if (cmd == TIOCGSERIAL) {
		struct serial_struct tmp;

		if (!arg)
			return -EFAULT;

		memset(&tmp, 0, sizeof(tmp));

		tmp.type		= tty0tty->serial.type;
		tmp.line		= tty0tty->serial.line;
		tmp.port		= tty0tty->serial.port;
		tmp.irq			= tty0tty->serial.irq;
		tmp.flags		= ASYNC_SKIP_TEST | ASYNC_AUTO_IRQ;
		tmp.xmit_fifo_size	= tty0tty->serial.xmit_fifo_size;
		tmp.baud_base		= tty0tty->serial.baud_base;
		tmp.close_delay		= 5*HZ;
		tmp.closing_wait	= 30*HZ;
		tmp.custom_divisor	= tty0tty->serial.custom_divisor;
		tmp.hub6		= tty0tty->serial.hub6;
		tmp.io_type		= tty0tty->serial.io_type;

		if (copy_to_user((void __user *)arg, &tmp, sizeof(struct serial_struct)))
			return -EFAULT;
		return 0;
	}
	return -ENOIOCTLCMD;
}

static int tty0tty_ioctl_tiocmiwait(struct tty_struct *tty, struct file *file,
                      unsigned int cmd, unsigned long arg)
{
	struct tty0tty_serial *tty0tty = tty->driver_data;
	
#ifdef SCULL_DEBUG
        printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	if (cmd == TIOCMIWAIT) {
		DECLARE_WAITQUEUE(wait, current);
		struct async_icount cnow;
		struct async_icount cprev;

		cprev = tty0tty->icount;
		while (1) {
			add_wait_queue(&tty0tty->wait, &wait);
			set_current_state(TASK_INTERRUPTIBLE);
			schedule();
			remove_wait_queue(&tty0tty->wait, &wait);

			/* see if a signal woke us up */
			if (signal_pending(current))
				return -ERESTARTSYS;

			cnow = tty0tty->icount;
			if (cnow.rng == cprev.rng && cnow.dsr == cprev.dsr &&
			    cnow.dcd == cprev.dcd && cnow.cts == cprev.cts)
				return -EIO; /* no change => error */
			if (((arg & TIOCM_RNG) && (cnow.rng != cprev.rng)) ||
			    ((arg & TIOCM_DSR) && (cnow.dsr != cprev.dsr)) ||
			    ((arg & TIOCM_CD)  && (cnow.dcd != cprev.dcd)) ||
			    ((arg & TIOCM_CTS) && (cnow.cts != cprev.cts)) ) {
				return 0;
			}
			cprev = cnow;
		}

	}
	return -ENOIOCTLCMD;
}

static int tty0tty_ioctl_tiocgicount(struct tty_struct *tty, struct file *file,
                      unsigned int cmd, unsigned long arg)
{
	struct tty0tty_serial *tty0tty = tty->driver_data;
	
#ifdef SCULL_DEBUG
        printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	if (cmd == TIOCGICOUNT) {
		struct async_icount cnow = tty0tty->icount;
		struct serial_icounter_struct icount;

		icount.cts	= cnow.cts;
		icount.dsr	= cnow.dsr;
		icount.rng	= cnow.rng;
		icount.dcd	= cnow.dcd;
		icount.rx	= cnow.rx;
		icount.tx	= cnow.tx;
		icount.frame	= cnow.frame;
		icount.overrun	= cnow.overrun;
		icount.parity	= cnow.parity;
		icount.brk	= cnow.brk;
		icount.buf_overrun = cnow.buf_overrun;

		if (copy_to_user((void __user *)arg, &icount, sizeof(icount)))
			return -EFAULT;
		return 0;
	}
	return -ENOIOCTLCMD;
}

static int tty0tty_ioctl(struct tty_struct *tty, struct file *file,
                      unsigned int cmd, unsigned long arg)
{
#ifdef SCULL_DEBUG
	printk(KERN_DEBUG "%s - %04X \n", __FUNCTION__,cmd);
#endif
	switch (cmd) {
	case TIOCGSERIAL:
		return tty0tty_ioctl_tiocgserial(tty, file, cmd, arg);
	case TIOCMIWAIT:
		return tty0tty_ioctl_tiocmiwait(tty, file, cmd, arg);
	case TIOCGICOUNT:
		return tty0tty_ioctl_tiocgicount(tty, file, cmd, arg);
	}

	return -ENOIOCTLCMD;
}

static struct tty_operations serial_ops = {
	.open = tty0tty_open,
	.close = tty0tty_close,
	.write = tty0tty_write,
	.write_room = tty0tty_write_room,
	.set_termios = tty0tty_set_termios,
	.tiocmget = tty0tty_tiocmget,
	.tiocmset = tty0tty_tiocmset,
	.ioctl = tty0tty_ioctl,
};

static struct tty_driver *tty0tty_tty_driver;

static int __init tty0tty_init(void)
{

	int retval;
#ifdef SCULL_DEBUG
	printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	/* allocate the tty driver */
	tty0tty_tty_driver = alloc_tty_driver(TINY_TTY_MINORS);
	if (!tty0tty_tty_driver)
		return -ENOMEM;

	/* initialize the tty driver */
	tty0tty_tty_driver->owner = THIS_MODULE;
	tty0tty_tty_driver->driver_name = "tty0tty";
	tty0tty_tty_driver->name = "tnt";
        /* no more devfs subsystem */
	tty0tty_tty_driver->major = TINY_TTY_MAJOR;
	tty0tty_tty_driver->type = TTY_DRIVER_TYPE_SERIAL;
	tty0tty_tty_driver->subtype = SERIAL_TYPE_NORMAL;
        tty0tty_tty_driver->flags = TTY_DRIVER_RESET_TERMIOS | TTY_DRIVER_REAL_RAW ;
        /* no more devfs subsystem */
	tty0tty_tty_driver->init_termios = tty_std_termios;
        tty0tty_tty_driver->init_termios.c_iflag = 0;
        tty0tty_tty_driver->init_termios.c_oflag = 0;
        tty0tty_tty_driver->init_termios.c_cflag = B38400 | CS8 | CREAD;
        tty0tty_tty_driver->init_termios.c_lflag = 0;
        tty0tty_tty_driver->init_termios.c_ispeed = 38400;
        tty0tty_tty_driver->init_termios.c_ospeed = 38400;


	tty_set_operations(tty0tty_tty_driver, &serial_ops);


	/* register the tty driver */
	retval = tty_register_driver(tty0tty_tty_driver);
	if (retval) {
		printk(KERN_ERR "failed to register tty0tty tty driver");
		put_tty_driver(tty0tty_tty_driver);
		return retval;
	}

	printk(KERN_INFO DRIVER_DESC " " DRIVER_VERSION);
	return retval;
}

static void __exit tty0tty_exit(void)
{
	struct tty0tty_serial *tty0tty;
	int i;
	
#ifdef SCULL_DEBUG
        printk(KERN_DEBUG "%s - \n", __FUNCTION__);
#endif
	for (i = 0; i < TINY_TTY_MINORS; ++i)
		tty_unregister_device(tty0tty_tty_driver, i);
	tty_unregister_driver(tty0tty_tty_driver);

	/* shut down all of the timers and free the memory */
	for (i = 0; i < TINY_TTY_MINORS; ++i) {
		tty0tty = tty0tty_table[i];
		if (tty0tty) {
			/* close the port */
			while (tty0tty->open_count)
				do_close(tty0tty);

			/* shut down our timer and free the memory */
			kfree(tty0tty);
			tty0tty_table[i] = NULL;
		}
	}
}

module_init(tty0tty_init);
module_exit(tty0tty_exit);
