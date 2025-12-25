from backend import gdbmi

class SymbolsManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI
