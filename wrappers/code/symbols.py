from backend import gdbmi

class SymbolsManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI

    def showStackVariables(self):
        return self.gdbMI.sendCmd("-stack-list-variables --all-values")
    
    def getVariableValue(self, varName: str):
        return self.gdbMI.sendCmd(f"-data-evaluate-expression {varName}")