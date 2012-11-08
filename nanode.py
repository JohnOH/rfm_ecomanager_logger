from __future__ import print_function
import serial
import json

class NanodeError(Exception):
    """Base class for errors from the Nanode."""


class NanodeRestart(NanodeError):
    """Nanode has restarted."""
    

class Nanode(object):
    """Used to manage a Nanode running the rfm_edf_ecomanager code."""
    
    def __init__(self, args, port="/dev/ttyUSB0"):
        self.port = port
        self.args = args
        self._open_port()
        try:
            self.send_init_commands()
        except NanodeRestart:
            self.send_init_commands() # re-send init commands after restart
        
    def send_init_commands(self):
        print("Sending init commands to Nanode...")
        self.send_command("v", 4) # don't show any debug log messages
        self.send_command("m") # manual pairing mode
        if self.args.promiscuous:
            self.send_command("u") # print data from all valid transmitters
        else:
            self.send_command("k") # Only print data from known transmitters        
        
    def readjson(self):
        while True:
            line = self._readline()
            if line[0] == "{":
                json_line = json.loads(line)
                break
        return json_line
        
    def _readline(self):
        try_again = True
        while try_again:
            line = self.serial.readline()
            print("Nanode:", line, end="")            
            if line.strip() == "EDF IAM Receiver":
                try_again = True
            elif line.strip() == "Finished init":
                print("Nanode restart detected")
                raise NanodeRestart()
                try_again = True
            else:
                try_again = False            
        return line
        
    def _open_port(self):
        print("Opening port", self.port)
        self.serial = serial.Serial(self.port, 115200)
        # Deliberately don't catch exception: if connecting to the 
        # Serial port fails then we need to terminate.
        
    def send_command(self, cmd, param=None):
        # print("send_command(cmd=", cmd, ", param=", param, ")")
        self.serial.flushInput()
        self.serial.write(cmd)
        self._process_response()
        if param:
            self.serial.write(str(param) + "\r")
            echo = self.serial.readline()
            if echo.strip() != str(param):
                raise NanodeError("Attempted to send command {:s}{:d}, "
                                  "received incorrect echo: {:s}"
                                  .format(cmd, param, echo))
            self._process_response()
                  
    def _process_response(self):
        response = self._readline()            
        if response.split()[0] != "ACK":
            raise NanodeError(response)
