from backend import gdbmi

class CodeManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI

    # NOTE: if it's an address, put * before it
    def setBreakpoint(self, position: str):
        try:
            address = int(position)
        except ValueError:
            return self.gdbMI.sendCmd(f"-break-insert {position}")
        
        return self.gdbMI.sendCmd(f"-break-insert *{str(hex(address))}")

    def continueExecution(self):
        self.gdbMI.sendCmd("-exec-continue")

        return self.gdbMI.readResponse(-1)
