from pygdbmi import constants
from pygdbmi.gdbcontroller import GdbController

class gdbPipe:
    def __init__(self, gdbArgs: list[str]):
        if (not gdbArgs):
            raise ValueError("No GDB parameters given")
        
        gdbCommand = ["gdb", "--interpreter=mi2"]
        gdbCommand.extend(gdbArgs)

        print(gdbCommand)
        
        self.gdbmi = GdbController(command=gdbCommand)

    def sendCmd(self, command: str):
        responses = self.gdbmi.write(command)
        return responses
    
    def quit(self):
        return self.sendCmd("-gdb-exit")
