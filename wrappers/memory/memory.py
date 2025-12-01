from backend import gdbmi

class MemoryManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI

    def readMemory(self, address: str, offset: int = 0, count: int = 1):
        return self.gdbMI.sendCmd(f"-data-read-memory-bytes -o {offset} {address} {count}")