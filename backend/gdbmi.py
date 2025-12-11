from pygdbmi import constants
from pygdbmi.gdbcontroller import GdbController

class GdbChannel:
    def __init__(self, gdbArgs: list[str]):
        gdbCommand = ["gdb", "--interpreter=mi2"]
        
        if (gdbArgs):
            gdbCommand.extend(gdbArgs)

        # print(gdbCommand)

        self.gdbmi = GdbController(command=gdbCommand)

    def readResponse(self, attempts: int):
        att = attempts
        responses = None
        while True:
            try:
                responses = self.gdbmi.get_gdb_response(timeout_sec=1)
            except constants.GdbTimeoutError:
                print("Waiting...")
                if (att > 0):
                    att -= 1

                if (att == 0):
                    print("No more attempts.")
                    return None
                
                if (att == -1):
                    continue
            
            return responses

    def sendCmd(self, command: str):
        return self.gdbmi.write(command)
    
    def flush(self):
        return self.readResponse(-1)
    
    def quit(self):
        return self.sendCmd("-gdb-exit")
