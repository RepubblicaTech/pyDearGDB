from backend.gdbmi import GdbChannel
from wrappers.code import symbols, code
from wrappers.memory import memory
from wrappers.cpu import cpu

from pprint import pprint

import dearpygui.dearpygui as dpg

class pyGDBApp:
    SHORTCUT_GDBCONFIG = 'Ctrl+G'
    SHORTCUT_BREAKMAN = 'Ctrl+B'
    SHORTCUT_CONTINUE = 'F5'
    SHORTCUT_STEPOVER = 'F10'
    SHORTCUT_STEPINTO = 'F11'
    SHORTCUT_STEPOVERASM = 'Alt+F10'
    SHORTCUT_STEPINTOASM = 'Alt+F11'
    SHORTCUT_STEPOUT = 'Shift+F11'
    SHORTCUT_CODEVIEW = 'Ctrl+L'
    
    COLOR_RED = (229, 38, 32, 255)
    COLOR_GREEN = (41, 196, 21, 255)
    COLOR_ORANGE = (237, 136, 14, 255)
    
    LOC_THRESHOLD = 15     # how many lines of code to show
    
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
        
        self.breakpointTags: list[str] = []
        self.locTags: list[str] = []
        
        self.currentFile = ""
        self.currentLine = 0
        self.fileStart = 0
        self.fileEnd = 0
        self.currentAddress = 0x0
                
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
        self.waiting = True
        print("CONTINUING EXECUTION...")
        response = self.gbdCodeManager.continueExecution()
        print("OK")
        self.updateEverything(response)
        
    def sendStepOver(self):
        self.waiting = True
        print("STEPOVER...")
        
        response = self.gbdCodeManager.stepOver()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        print("OK")
        self.updateEverything(response)
        
    def sendStepInto(self):
        self.waiting = True
        print("STEPINTO...")
        response = self.gbdCodeManager.stepInto()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        print("OK")
        self.updateEverything(response)
        
    def sendStepOut(self):
        self.waiting = True
        print("STEPOUT...")
        response = self.gbdCodeManager.stepOut()
        while (response[-1]["message"] == "running"):
            response = self.gdbMI.readResponse(-1)
        
        print("OK")
        self.updateEverything(response)
        
    def create(self):
        dpg.create_viewport(title='dearGDB', width=1200, height=818)
        dpg.set_viewport_clear_color([83, 226, 117, 255])
        
        self.appMenu = dpg.viewport_menu_bar()
        
        self.symWindow = dpg.window(label="Variables", width=200, height=400)
        self.stackWindow = dpg.window(label="Stack", pos=(200, 18), width=200, height=400)
        self.codeWindow = dpg.window(label="Code View", pos=(400, 18), width=800, height=500)
        
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
                
        with dpg.window(label="Breakpoints manager", modal=True, tag="breakman_window", show=False, width=300):
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
                    dpg.add_menu_item(label="Toggle code/disassembly", shortcut=self.SHORTCUT_CODEVIEW)
                    
            with dpg.group(tag="code_view"):
                pass

        with self.cpuWindow:
            dpg.add_text("CPU registers")
            
        with self.stackWindow:
            dpg.add_text("Stack view")
            
        with self.symWindow:
            dpg.add_text("Variables")
            
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

        # initialise keyboard shortcuts
        with dpg.handler_registry():
            dpg.add_key_press_handler(dpg.mvKey_F5, callback=self.sendContinueExec)
            dpg.add_key_press_handler(dpg.mvKey_F10, callback=self.sendStepOver)
            dpg.add_key_press_handler(dpg.mvKey_F11, callback=self.sendStepInto)
            dpg.add_key_press_handler(dpg.mvKey_LShift | dpg.mvKey_F11, callback=self.sendStepOut)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        startup = self.gdbMI.readResponse(-1)
        for message in startup:
            if (message["type"] == "notify" and  message["message"] == "stopped"):
                print("Program stopped.")
                
        # initialise pre-existing breakpoints (if any)
        self.updateBreakpointsTable()
        
                
    def updateEverything(self, gdbMIResponse: list[dict]):
        self.updateCodeView(gdbMIResponse)
                
    def updateCodeView(self, gdbMIResponses: list[dict]):
        pprint(gdbMIResponses)
        
        context = {}
        for resp in gdbMIResponses:
            if resp["message"] == "stopped":
                context = resp["payload"]["frame"]
                
        if (context == {}):
            return
        
        # if we are still in the same file, we're just quitting
        if ((context["fullname"] == self.currentFile) and ((int(context["line"]) < self.fileEnd) and (int(context["line"]) > self.fileStart))):
            print("We're in the same file")
            
            if (self.currentLine != int(context["line"])):
                print(f"Unsetting LOC {self.currentLine}")
                # unset current LOC
                locTag = f"code_{self.currentLine}"
                dpg.configure_item(locTag, color=(255, 255, 255, 255))
                
                print(f"Setting LOC {int(context["line"])}")
                locTag = f"code_{int(context["line"])}"
                if (not dpg.does_item_exist(locTag)):
                    return
                dpg.configure_item(locTag, color=(212, 74, 74, 255))
                self.currentLine = int(context["line"])
            return
        
        
        # load the file
        if (not context["fullname"]):
            return
        
        print(f"Loading new file {context["file"]} (line {context["line"]})")

        with open(context["file"], "r") as sourceFile:
            if (not sourceFile):
                return
            
            self.currentFile = context["fullname"]
            self.currentLine = int(context["line"])
        
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
                    dpg.configure_item(locTag, color=(212, 74, 74, 255))
                    
            print("Done")
        
            sourceFile.close()
        
    def run(self):
        # TODO: some startup code (like, initialize the code/disassembly)
        
        while dpg.is_dearpygui_running():
            # TODO:
            #   - Update register values
            #       - for which we'd automatically update the stack in case RSP changes or something happens
            #   - Update code
            #   - Update variables
            #   - update memory
            
            dpg.render_dearpygui_frame()

        dpg.destroy_context()
