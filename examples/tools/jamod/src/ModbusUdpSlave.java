/**
 * Copyright 2002-2010 jamod development team
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/

package org.pymodbus;

import net.wimpi.modbus.Modbus;
import net.wimpi.modbus.ModbusCoupler;
import net.wimpi.modbus.net.ModbusUDPListener;
import net.wimpi.modbus.procimg.*;
import net.wimpi.modbus.util.SerialParameters;


/**
 * Class implementing a simple Modbus slave.
 * A simple process image is available to test
 * functionality and behaviour of the implementation.
 *
 * @author Galen Collins
 * @version @version@ (@date@)
 */
public class ModbusUdpSlave {

  public static void main(String[] args) {

    ModbusUDPListener listener = null;
    SimpleProcessImage spi = new SimpleProcessImage();
    int port = Modbus.DEFAULT_PORT;

    if (Modbus.debug) System.out.println("jModbus Modbus UDP Slave");
    if (args != null && args.length >= 1) {
        port = Integer.parseInt(args[0]);
    }
    
    try {

      //1. Prepare a process image
      spi = new SimpleProcessImage();
      spi.addDigitalOut(new SimpleDigitalOut(true));
      spi.addDigitalOut(new SimpleDigitalOut(false));
      spi.addDigitalIn(new SimpleDigitalIn(false));
      spi.addDigitalIn(new SimpleDigitalIn(true));
      spi.addDigitalIn(new SimpleDigitalIn(false));
      spi.addDigitalIn(new SimpleDigitalIn(true));
      spi.addRegister(new SimpleRegister(251));
      spi.addInputRegister(new SimpleInputRegister(45));

      //2. Create the coupler and set the slave identity
      ModbusCoupler.getReference().setProcessImage(spi);
      ModbusCoupler.getReference().setMaster(false);
      ModbusCoupler.getReference().setUnitID(2);

      //3. Create a listener with 3 threads
      listener = new ModbusUDPListener();
      listener.setPort(port);
      listener.start();

    } catch (Exception ex) {
      ex.printStackTrace();
    }
  }//main

}

