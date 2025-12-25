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
        
        self.breakpointTags = []
                
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
                
    def sendContinueExec(self):
        self.waiting = True
        self.gbdCodeManager.continueExecution()
        
    def sendStepOver(self):
        self.waiting = True
        self.gbdCodeManager.stepOver()
        
    def sendStepInto(self):
        self.waiting = True
        self.gbdCodeManager.stepInto()
        
    def sendStepOut(self):
        self.waiting = True
        self.gbdCodeManager.stepOut()
        
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

        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        self.busy: bool = True
        
        self.waiting = True
        startup = self.gdbMI.readResponse(-1)
        for message in startup:
            if (message["type"] == "notify" and  message["message"] == "stopped"):
                print("Program stopped.")
                
    # def updateCodeView(self):
        
    def run(self):
        # TODO: some startup code (like, initialize the code/disassembly)
        
        while dpg.is_dearpygui_running():
            # TODO:
            #   - Update register values
            #       - for which we'd automatically update the stack in case RSP changes or something happens
            #   - Update code
            #   - Update variables
            #   - (eventually) update memory
            
            if (self.waiting):
                # we were waiting for a breakpoint/next instruction
                # we will update everything
                self.waiting = False
            
            dpg.render_dearpygui_frame()

        dpg.destroy_context()
