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
import net.wimpi.modbus.net.ModbusSerialListener;
import net.wimpi.modbus.procimg.*;
import net.wimpi.modbus.util.SerialParameters;


/**
 * Class implementing a simple Modbus Serial slave.
 * A simple process image is available to test
 * functionality and behaviour of the implementation.
 *
 * @author Galen Collins
 * @version @version@ (@date@)
 */
public class ModbusSerialSlave {

  public static void main(String[] args) {

    ModbusSerialListener listener = null;
    SimpleProcessImage spi = new SimpleProcessImage();
    String portname = args[0];

    if (Modbus.debug) System.out.println("jModbus Modbus Serial Slave");
    
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

      //3. Set up serial parameters
      SerialParameters params = new SerialParameters();
      params.setPortName(portname);
      params.setBaudRate(9600);
      params.setDatabits(8);
      params.setParity("None");
      params.setStopbits(1);
      params.setEncoding("bin");
      params.setEcho(false);
      if (Modbus.debug) System.out.println("Encoding [" + params.getEncoding() + "]");

      //4. Set up serial listener
      listener = new ModbusSerialListener(params);
      listener.setListening(true);

    } catch (Exception ex) {
      ex.printStackTrace();
    }
  }//main

}

