#!/usr/bin/env python

# Send raw bytes over socket to reproduce error causing apu/pdus of
# https://github.com/riptideio/pymodbus/issues/232

import os
import socket
import sys
import time

def main():

    # an array of arrays of bytearrays containing malformed, fragmented or incomplete modbus APUs
    error_bytes=[]

    # test apu #0, fragment of frame, incomplete header
    error_bytes.insert(0,[b"\x00\x13\x00\x00\x00"])
    
    # test apu #1, complete frame, fragmented in data 
    error_bytes.insert(1,[b"\x00\x0d\x00\x00\x00\x06\x01\x01",b"\x00\x00\x00\x01"])
    
    # test apu #2, complete frame, fragmented in header
    error_bytes.insert(2,[b"\x00\x00\x00\x00\x00\x1d",
        b"\x01\x10\x00\x00\x00\x0b\x16\x33\xfe\x00\x6f\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"])
    # test apu #3, two frames, second fragmented around data
    error_bytes.insert(3,[b"\x00\x0d\x00\x00\x00\x06\x01\x01\x00\x00\x00\x01\x00\x0d\x00\x00\x00\x06\x01\x01",
        b"\x00\x00\x00\x01"])
    # test apu #4, two frames, read coils and write registers, with junk bytes following the first frame
    error_bytes.insert(4,[b"\x00\x00\x00\x00\x00\x06\xfc\x01\x00\x02\x00\x03",b"\xe0\xdf\x09",b"\x00\x01\x00\x00\x00\x0b\xfc\x10\x00\x20\x00\x02\x04\x0a\x07\x10\xb4"]) 

    # test apu #5, set trio float32 values, fragmented in data
    error_bytes.insert(5,[b"\x05\x8e\x00\x00\x00\x1f\x01\x10\x00\x00\x00\x0c\x18\x00\x00\x00\x00\x00\x00\x3f\x80\x00\x00\x40\x00\x00\x00\x40\x40\x00\x00",b"\x40\x80\x00\x00\x40\xa0"])

    # service under test
    server_addr=('192.168.0.100',8020)

    # run all tests
    #for err_index in range(len(error_bytes)):
    # or select a specific test
    for err_index in [5]:

        print("test packet #{} :\n\n{}".format(err_index,error_bytes[err_index]))
        bytes_to_send=error_bytes[err_index]


        mdbclient_sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mdbclient_sock.settimeout(0.1)
        mdbclient_sock.connect(server_addr)

        svr_resp_bytes=bytes()
        for bytes_chunk in bytes_to_send:
            print("Sending '{}'...".format(bytes_chunk))
            try:
                mdbclient_sock.sendall(bytes_chunk)
                svr_resp_bytes=mdbclient_sock.recv(256)
            except OSError as e:
                print("Os error: {}".format(str(e)))
                pass
            except socket.timeout:
                print("Socket timed out...")
                pass

            if len(svr_resp_bytes)>0:
                print("Response '{}'".format(svr_resp_bytes))
            else:
                print("No response")

            # can't control when tcp will send a segment, but pausing momentarily makes it
            # more likely that the stack will send each 'bytes_chunk' independently,
            # reproducing the error(s)
            time.sleep(0.1)

        mdbclient_sock.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
