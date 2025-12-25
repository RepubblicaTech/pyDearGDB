from backend import gdbmi

class CodeManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI

    def setBreakpoint(self, position: str):
        try:
            address = int(position)
        except ValueError:
            return self.gdbMI.sendCmd(f"-break-insert {position}")
        
        return self.gdbMI.sendCmd(f"-break-insert *{str(hex(address))}")
    
    def delBreakpoint(self, breakpointNumber: int):
        return self.gdbMI.sendCmd(f"-break-delete {breakpointNumber}")

    def getBreakpoints(self):
        return self.gdbMI.sendCmd("-break-list")
    
    def getBreakpointsList(self) -> list[dict]:
        breakpoints: list[dict] = []
        
        breakpointsResponse = self.getBreakpoints()[0]
        
        if (not breakpointsResponse["payload"]["BreakpointTable"]["body"]):
            print("No breakpoints set.")
            return None
        
        breakpointsBody = breakpointsResponse["payload"]["BreakpointTable"]["body"]
        
        for breakpoint in breakpointsBody:
            breakpoints.append({
                "bnum": breakpoint["number"],
                "where": f"{breakpoint["func"]}",
                "address": breakpoint["addr"],
                "file": breakpoint["file"],
                "fullpath": breakpoint["fullname"],
                "line": breakpoint["line"],
                "enabled": True if breakpoint["enabled"] == "y" else False
            })
        
        return breakpoints
        
    def continueExecution(self):
        self.gdbMI.sendCmd("-exec-continue")

        return self.gdbMI.readResponse(-1)
    
    def stepOver(self):
        self.gdbMI.sendCmd("-exec-next")
        return self.gdbMI.readResponse(-1)
    
    def stepOverInstruction(self):
        self.gdbMI.sendCmd("-exec-next-instruction")
        return self.gdbMI.readResponse(-1)
        
    def stepInto(self):
        self.gdbMI.sendCmd("-exec-step")
        return self.gdbMI.readResponse(-1)
    
    def stepIntoInstruction(self):
        self.gdbMI.sendCmd("-exec-step-instruction")
        return self.gdbMI.readResponse(-1)
    
    def stepOut(self):
        self.gdbMI.sendCmd("-exec-finish")
        return self.gdbMI.readResponse(-1)
    