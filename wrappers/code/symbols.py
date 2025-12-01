from backend import gdbmi

class CodeManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI

    # NOTE: if it's an address, put * before it
    def setBreakpoint(self, position: str):
        return self.gdbMI.sendCmd(f"-break-insert {position}")

    def continueExecution(self):
        return self.gdbMI.sendCmd("-exec-continue", -1)
