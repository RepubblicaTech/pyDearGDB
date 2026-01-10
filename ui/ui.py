from backend.gdbmi import GdbChannel
from wrappers.code import symbols, code
from wrappers.memory import memory
from wrappers.cpu import cpu

from pprint import pprint

import dearpygui.dearpygui as dpg

from threading import Thread

class pyGDBApp:
    SHORTCUT_GDBCONFIG = 'Ctrl+G'
    SHORTCUT_BREAKMAN = 'Ctrl+B'
    SHORTCUT_CONTINUE = 'F5'
    SHORTCUT_STEPOVER = 'F10'
    SHORTCUT_STEPINTO = 'F11'
    SHORTCUT_NEXTASM = 'Alt+F10'
    SHORTCUT_STEPINTOASM = 'Alt+F11'
    SHORTCUT_STEPOUT = 'Shift+F11'
    SHORTCUT_CODEVIEW = 'Ctrl+L'
    
    COLOR_RED = (229, 38, 32, 255)
    COLOR_GREEN = (41, 196, 21, 255)
    COLOR_ORANGE = (237, 136, 14, 255)
    
    LOC_THRESHOLD = 10     # how many lines of code to show
    
    def __init__(self, gdbMI: GdbChannel, title="application"):
        dpg.create_context()
        self.appTitle = title
        
        self.gdbSymManager = symbols.SymbolsManager(gdbMI)
        self.gbdCodeManager = code.CodeManager(gdbMI)
        self.gdbMemManager = memory.MemoryManager(gdbMI)
        self.gdbCPUManager = cpu.CPUManager(gdbMI)
        
        self.gdbMI = gdbMI
        
        self.sourceCode = True # check if we're debugging code
        self.waiting = False # waiting for breakpoint/next step
        
        self.currentFile = ""
        self.currentLine = 0
        self.fileStart = 0
        self.fileEnd = 0
        self.breakpointTags: list[str] = []
        self.locTags: list[str] = []
        
        self.currentFunction = ""
        
        self.disasmStart = 0x0
        self.currentDisasmAddress = 0x0
        self.disasmEnd = 0x0
        self.disasmTags: list[str] = []
                
    def updateBreakpointsTable(self):
        breakpoints = self.gbdCodeManager.getBreakpointsList()
        pprint(breakpoints)
        
        self.breakpointTags.clear()
        
        if (breakpoints):
            for breakpoint in breakpoints:
                rowTag = f"break_{breakpoint["bnum"]}"
                # ignore if tag already exists
                if (dpg.does_item_exist(rowTag)):
                    continue

                self.breakpointTags.append(rowTag)
                with dpg.table_row(parent="breakpoints_table", tag=rowTag):
                    dpg.add_text(breakpoint["bnum"])
                    dpg.add_text(breakpoint["address"])
                    dpg.add_text(breakpoint["where"])
                    dpg.add_text(f"{breakpoint["file"]}:{breakpoint["line"]}")
                    
    def sendAddBreakpoint(self):
        where = dpg.get_value(self.breakpointWhere)
        response = self.gbdCodeManager.setBreakpoint(where)
        print(f"ADDING BREAKPOINT @ {where}")
        pprint(response[0])
        
        match response[0]["message"]:
            case "done":
                bpNumber = int(response[0]["payload"]["bkpt"]["number"])
                dpg.configure_item(self.bpManStatusText, color=self.COLOR_GREEN)
                dpg.set_value(self.bpManStatusText, f"Breakpoint set successfully [{bpNumber}].")
                
                self.updateBreakpointsTable()
            case "error":
                dpg.configure_item(self.bpManStatusText, color=self.COLOR_RED)
                dpg.set_value(self.bpManStatusText, f"An error occurred: {response[0]["payload"]["msg"]}")
                
            case _:
                dpg.configure_item(self.bpManStatusText, color=self.COLOR_ORANGE)
                dpg.set_value(self.bpManStatusText, "Unknown status, check console for details.")
                
    def sendRemBreakpoint(self):
        bNumber = int(dpg.get_value(self.breakpointToDelete))
        response = self.gbdCodeManager.delBreakpoint(bNumber)
        print(f"REMOVING BREAKPOINT {bNumber}")
        pprint(response[0])
        
        match response[0]["message"]:
            case None:
                dpg.configure_item(self.bpManStatusText, color=self.COLOR_RED)
                dpg.set_value(self.bpManStatusText, f"An error occurred: {response[0]["payload"]["msg"]}")
            case "done":
                dpg.configure_item(self.bpManStatusText, color=self.COLOR_GREEN)
                dpg.set_value(self.bpManStatusText, f"Breakpoint {bNumber} removed successfully.")
                
                rowTag = f"break_{bNumber}"
                dpg.delete_item(rowTag)
                self.breakpointTags.remove(rowTag)
                
                self.updateBreakpointsTable()
                
    # TODO: change the way we step if we're in source view or disassembly view
                
    def sendContinueExec(self):
        print("CONTINUING EXECUTION...")
        response = self.gbdCodeManager.continueExecution()
        self.updateEverything(response)
        print("...OK")
        
    def sendStepOver(self):
        print("STEPOVER...")
        
        response = self.gbdCodeManager.stepOver()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        self.updateEverything(response)
        print("...OK")
        
    def sendNextInstruction(self):
        print("NEXT INSTRUCTION...")
        
        response = self.gbdCodeManager.nextInstruction()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        self.updateEverything(response)
        print("...OK")
        
    def sendStepInto(self):
        print("STEPINTO...")
        response = self.gbdCodeManager.stepInto()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        self.updateEverything(response)
        print("...OK")
        
    def sendStepInstruction(self):
        print("STEP INSTRUCTION...")
        
        response = self.gbdCodeManager.stepInstruction()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        self.updateEverything(response)
        print("...OK")
        
    def sendStepOut(self):
        print("STEPOUT...")
        response = self.gbdCodeManager.stepOut()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        self.updateEverything(response)
        print("...OK")
        
    def toggleCodeDisasm(self):
        self.sourceCode = not self.sourceCode
        windowTitle = f"{"Source code" if self.sourceCode else "Disassembly"} view"
        dpg.configure_item("code_window", label=windowTitle)
        self.updateSourceView(None, self.sourceCode)
        
    def create(self):
        dpg.create_viewport(title='dearGDB', width=1200, height=818)
        dpg.set_viewport_clear_color([83, 226, 117, 255])
        
        self.appMenu = dpg.viewport_menu_bar()
        
        self.symWindow = dpg.window(label="Variables", width=200, height=400)
        self.stackWindow = dpg.window(label="Stack", pos=(200, 18), width=200, height=400)
        self.codeWindow = dpg.window(label="Source code View", pos=(400, 18), width=800, height=500, tag="code_window")
        
        self.cpuWindow = dpg.window(label="CPU Registers", pos=(0, 418), width=400, height=400)
        self.memWindow = dpg.window(label="Memory", pos=(400, 518), width=800, height=300)
        
        with self.appMenu:
            with dpg.menu(label="File"):
                # to potentially set up GDB from the GUI
                dpg.add_menu_item(label="GDB Configuration", shortcut=self.SHORTCUT_GDBCONFIG)
                
            with dpg.menu(label="Debug"):
                dpg.add_menu_item(label="Manage breakpoints", shortcut=self.SHORTCUT_BREAKMAN, callback=lambda: dpg.configure_item("breakman_window", show=True))
                dpg.add_menu_item(label="Continue execution", shortcut=self.SHORTCUT_CONTINUE, callback=self.sendContinueExec)
                dpg.add_menu_item(label="Step over", shortcut=self.SHORTCUT_STEPOVER, callback=self.sendStepOver)
                dpg.add_menu_item(label="Step into", shortcut=self.SHORTCUT_STEPINTO, callback=self.sendStepInto)
                dpg.add_menu_item(label="Step out", shortcut=self.SHORTCUT_STEPOUT, callback=self.sendStepOut)
                dpg.add_menu_item(label="Next instruction", shortcut=self.SHORTCUT_NEXTASM, callback=self.sendNextInstruction)
                dpg.add_menu_item(label="Step instruction", shortcut=self.SHORTCUT_STEPINTOASM, callback=self.sendStepInstruction)
                
        with dpg.window(label="Breakpoints manager", modal=True, tag="breakman_window", show=False, height=400, width=500):
            self.breakpointsTable = dpg.table(label="Breakpoints", header_row=True, tag="breakpoints_table", policy=dpg.mvTable_SizingStretchProp)
            with self.breakpointsTable:
                dpg.add_table_column(label="B. number", width_fixed=False)
                dpg.add_table_column(label="Address", width_fixed=False)
                dpg.add_table_column(label="Function", width_fixed=False)
                dpg.add_table_column(label="File:line", width_fixed=False)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Where?")
                self.breakpointWhere = dpg.add_input_text(width=150)
            dpg.add_button(label="Insert breakpoint", callback=self.sendAddBreakpoint)
            
            dpg.add_spacer(height=20)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Breakpoint number:")
                self.breakpointToDelete = dpg.add_input_int(width=60)
            dpg.add_button(label="Remove breakpoint", callback=self.sendRemBreakpoint)
            
            self.bpManStatusText = dpg.add_text("")
            dpg.add_button(label="Close", callback=lambda: dpg.configure_item("breakman_window", show=False))
        
        with self.codeWindow:
            with dpg.menu_bar():
                with dpg.menu(label="View"):
                    dpg.add_menu_item(label="Toggle code/disassembly", shortcut=self.SHORTCUT_CODEVIEW, callback=self.toggleCodeDisasm)
                    
            with dpg.group(tag="code_view"):
                pass

        with self.cpuWindow:
            with dpg.group(tag="cpu_regs"):
                pass
            
        with self.stackWindow:
            dpg.add_text("Stack view")
            
        with self.symWindow:
            dpg.add_input_text(hint="variable name", width=150)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Show")
                dpg.add_button(label="Clear output")
            with dpg.group(tag="variables_group"):
                pass
            
        with self.memWindow:
            with dpg.menu_bar():
                with dpg.menu(label="View"):
                    dpg.add_input_text(label="Address")
                    dpg.add_slider_int(label="Bytes per row", min_value=1, max_value=32)
                    dpg.add_button(label="Show")
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=500, height=-1, border=True):
                    dpg.add_text("Raw memory bytes")

                # Bottom half
                with dpg.child_window(width=200, height=-1, border=True):
                    dpg.add_text("ASCII")

        # TODO: keyboard shortcuts
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        startup = self.gdbMI.readResponse(-1)
        for message in startup:
            if (message["type"] == "notify" and  message["message"] == "stopped"):
                print("Program stopped.")
                
        # initialise pre-existing breakpoints (if any)
        self.updateBreakpointsTable()
                
    def updateEverything(self, gdbMIResponses: list[dict]):
        context = {}
        
        if (gdbMIResponses):
            pprint(gdbMIResponses)

            for resp in gdbMIResponses:
                if resp["message"] == "stopped":
                    context = resp["payload"]["frame"]

            if (context == {}):
                return

        else:
            responses = self.gdbCPUManager.getThreadInfo()
            pprint(responses)
            for response in responses:
                if (response["type"] == "result" and response["message"] == "done"):
                    payload = response["payload"]
            
            if (not payload):
                return
            
            currentThread = payload["current-thread-id"]
            
            for thread in payload["threads"]:
                if thread["id"] != currentThread:
                    continue
                
                context = thread["frame"]
                
            if (context == {}):
                return
        
        self.updateSourceView(context, self.sourceCode)
        self.updateCPURegs()
        
        # sourceThread = Thread(target=self.updateSourceView, args=(gdbMIResponse, self.sourceCode))
        # regsThread = Thread(target=self.updateCPURegs)
        
        # sourceThread.start()
        # regsThread.start()
        
        # regsThread.join()
        # sourceThread.join()

    def updateCPURegs(self):
        # get register names
        regNames: list = []
        responses = self.gdbCPUManager.getRegisterNames()
        for response in responses:
            if (response["message"] == "done" and response["type"] == "result"):
                regNames = response["payload"]["register-names"]
        # get register values
        regValues: list[dict] = []
        responses = self.gdbCPUManager.getRegisterValues()
        for response in responses:
            if (response["message"] == "done" and response["type"] == "result"):
                regValues = response["payload"]["register-values"]
        
        changedRegs: list = []
        # get changed regs
        responses = self.gdbCPUManager.showUpdatedRegisters()
        for response in responses:
            if (response["message"] == "done" and response["type"] == "result"):
                changedRegs = response["payload"]["changed-registers"]
        
        for regValue in regValues:
            regNumber = regValue["number"]
            regValue = regValue["value"]
            
            try:
                changedRegs.index(regNumber)
                # if we don't get ValueError, then we just set the color for the label
                labelColor = self.COLOR_RED
            except ValueError:
                labelColor = (255, 255, 255, 255)
            
            regName = regNames[int(regNumber)]
            
            # make a label for each register
            regLabel = f"{regName}={regValue}"
            # make it a nice text :)
            regTag = f"reg_{regName}"
            if (dpg.does_item_exist(regTag)):
                dpg.set_value(regTag, regLabel)
                dpg.configure_item(regTag, color=labelColor)
            else:
                dpg.add_text(regLabel, parent="cpu_regs", tag=regTag, color=labelColor)

    def updateSourceView(self, currentFrame: dict, viewSource: bool):
        if (not currentFrame):
            return

        if (viewSource):
            # hide disasm tags
            for tag in self.disasmTags:
                dpg.configure_item(tag, show=False)
                
            # show source tags
            for tag in self.locTags:
                dpg.configure_item(tag, show=True)
            
            if ((currentFrame["file"] == self.currentFile) and ((int(currentFrame["line"]) < self.fileEnd) and (int(currentFrame["line"]) > self.fileStart))):
            # if we are still in the same file, we're just quitting
                print("We're in the same file")
                
                if (self.currentLine != int(currentFrame["line"])):
                    print(f"Unsetting LOC {self.currentLine}")
                    # unset current LOC
                    locTag = f"code_{self.currentLine}"
                    dpg.configure_item(locTag, color=(255, 255, 255, 255))
                    
                    print(f"Setting LOC {int(currentFrame["line"])}")
                    locTag = f"code_{int(currentFrame["line"])}"
                    if (not dpg.does_item_exist(locTag)):
                        return
    
                    dpg.configure_item(locTag, color=self.COLOR_RED)
                    self.currentLine = int(currentFrame["line"])
                return
            
            self.currentFile = currentFrame["file"]
            self.currentLine = int(currentFrame["line"])            
            
            # load the file
            if (not currentFrame["fullname"]):
                return

            print(f"Loading new file {currentFrame["file"]} (line {currentFrame["line"]})")

            sourceFile = open(currentFrame["fullname"], "r")

            if (not sourceFile):
                return

            # remove all current lines
            for tag in self.locTags:
                dpg.delete_item(tag)
            self.locTags.clear()

            offset = self.currentLine - self.LOC_THRESHOLD if (self.currentLine - self.LOC_THRESHOLD > 0) else 1

            print(f"Starting @ line {offset}")

            # so, this reads ALL lines, and returns eveything from the offset we wanted
            usefulLOCs = sourceFile.readlines()[(offset - 1):(self.currentLine + self.LOC_THRESHOLD)]
            self.fileStart = offset
            self.fileEnd = self.currentLine + self.LOC_THRESHOLD

            for i in range(0, len(usefulLOCs)):
                print(f"Line {i + offset}")
                # read a line
                loc = usefulLOCs[i]

                # create the label
                locTag = f"code_{i + offset}"
                if (dpg.does_item_exist(locTag)):
                    dpg.set_value(locTag, loc)
                else:
                    dpg.add_text(loc, parent="code_view", tag=locTag)
                    self.locTags.append(locTag)

                # highlight the current line
                if (i == (self.currentLine - offset)):
                    dpg.configure_item(locTag, color=self.COLOR_RED)

                sourceFile.close()
        else:
            # hide source tags
            for tag in self.locTags:
                dpg.configure_item(tag, show=False)
                
            # show disasm tags
            for tag in self.disasmTags:
                dpg.configure_item(tag, show=True)
            
            # are we still inside the address range?
            print(f"disasm START CURRENT END: {hex(self.disasmStart)} {hex(self.currentDisasmAddress)} {hex(self.disasmEnd)}")
            print(f"disasm NOW: {currentFrame["addr"]}")
            
            if ((int(currentFrame["addr"], base=16) > self.disasmStart) and (int(currentFrame["addr"], base=16) < self.disasmEnd)):
                
                if (int(currentFrame["addr"], base=16) != self.currentDisasmAddress):
                    tag = f"asm_{self.currentDisasmAddress - self.disasmStart}"
                
                    print(f"Unsetting disassembly @ {hex(self.currentDisasmAddress)}")
                    dpg.configure_item(tag, color=(255, 255, 255, 255))
                    
                    tag = f"asm_{int(currentFrame["addr"], base=16) - self.disasmStart}"
                    if (not dpg.does_item_exist(tag)):
                        return
                    print(f"Setting disassembly @ {currentFrame["addr"]}")
                    dpg.configure_item(tag, color=self.COLOR_RED)
                    self.currentDisasmAddress = int(currentFrame["addr"], base=16)
                return
            
            self.currentDisasmAddress = int(currentFrame["addr"], base=16)
            
            # disassemble more memory
            self.disasmStart = (int(currentFrame["addr"], base=16) - (self.LOC_THRESHOLD))
            responses = self.gbdCodeManager.disassemble(self.disasmStart, (self.LOC_THRESHOLD * 8))
            
            pprint(responses)
            
            disassembly: list[dict] = []    # a list of disassembly dicts
            for response in responses:
                if response["type"] == "result" and response["message"] == "done":
                    disassembly = response["payload"]["asm_insns"]
                    
            if (not disassembly):
                return
            
            # delete previous disasm tags
            for tag in self.disasmTags:
                dpg.delete_item(tag)
            self.disasmTags.clear()
            
            # create the tags
            for instruction in disassembly:
                try:
                    functionName = instruction["func-name"]
                    offset = int(instruction["offset"], base=10)
                except KeyError:
                    functionName = "UNKNOWN"
                    offset = "XXX"
                address = int(instruction["address"], base=16)
                instruction = instruction["inst"]
                
                # add a newline if we're in a different function
                if (functionName != self.currentFunction):
                    instTag = f"asmnl_{address - self.disasmStart}"
                    if (dpg.does_item_exist(instTag)):
                        dpg.set_value(instTag, "")
                    else:
                        dpg.add_text("", parent="code_view", tag=instTag)
                        self.disasmTags.append(instTag)
                        
                    self.currentFunction = functionName
                
                # create the label
                instTag = f"asm_{address - self.disasmStart}"
                if (dpg.does_item_exist(instTag)):
                    dpg.set_value(instTag, f"{functionName}+{offset}:\t{instruction}")
                else:
                    dpg.add_text(f"{functionName}+{offset}:\t{instruction}", parent="code_view", tag=instTag)
                    self.disasmTags.append(instTag)
                    
                # highlight the current line
                if (address == self.currentDisasmAddress):
                    dpg.configure_item(instTag, color=self.COLOR_RED)
                    
            self.disasmEnd = int(disassembly[-1]["address"], base=16)

        
    def run(self):
        while dpg.is_dearpygui_running():
            # TODO:
            #   - Update register values
            #       - for which we'd automatically update the stack in case RSP changes or something happens
            #   - Update code
            #   - Update variables
            #   - update memory
            
            dpg.render_dearpygui_frame()

        dpg.destroy_context()
