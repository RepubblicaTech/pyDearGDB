from backend import gdbmi

class CPUManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI

    def viewRegisterNames(self):
        return self.gdbMI.sendCmd("-data-list-register-names")
    
    def viewRegisterValues(self):
        return self.gdbMI.sendCmd(f"-data-list-register-values x")