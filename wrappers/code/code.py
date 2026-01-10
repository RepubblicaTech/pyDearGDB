from backend import gdbmi

class CodeManager:
    def __init__(self, gdbMI: gdbmi.GdbChannel):
        if (not gdbMI):
            raise ValueError("Where is my GDB MI class?")
        
        self.gdbMI = gdbMI
        
    def disassemble(self, startAddress: int, bytes: int):
        endAddress = startAddress + bytes
        return self.gdbMI.sendCmd(f"-data-disassemble -s {startAddress} -e {endAddress}")

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
            breakpointDict = {
                "bnum": breakpoint["number"],
                "where": None,
                "address": breakpoint["addr"],
                "file": None,
                "fullpath": None,
                "line": None,
                "enabled": True if breakpoint["enabled"] == "y" else False
            }
            
            try:
                breakpointDict["where"] = f"{breakpoint["func"]}"
                
                breakpointDict["file"] = breakpoint["file"]
                breakpointDict["line"] = breakpoint["line"]
                breakpointDict["fullpath"] = breakpoint["fullname"]
            except KeyError:
                breakpointDict["where"] = f"{breakpoint["at"]}"
                breakpointDict["file"] = "???"
                breakpointDict["line"] = "???"
            
            breakpoints.append(breakpointDict)
        
        return breakpoints
        
    def continueExecution(self):
        self.gdbMI.sendCmd("-exec-continue")

        return self.gdbMI.readResponse(-1)
    
    def stepOver(self):
        return self.gdbMI.sendCmd("-exec-next")
    
    def nextInstruction(self):
        return self.gdbMI.sendCmd("-exec-next-instruction")
        
    def stepInto(self):
        return self.gdbMI.sendCmd("-exec-step")
    
    def stepInstruction(self):
        return self.gdbMI.sendCmd("-exec-step-instruction")
    
    def stepOut(self):
        return self.gdbMI.sendCmd("-exec-finish")
    