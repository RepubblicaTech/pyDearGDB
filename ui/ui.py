from backend.gdbmi import GdbChannel
from wrappers.code import symbols
from wrappers.memory import memory
from wrappers.cpu import cpu

import dearpygui.dearpygui as dpg

class pyGDBApp:
    SHORTCUT_GDBCONFIG = 'Ctrl+G'
    SHORTCUT_BREAKADD = 'Ctrl+B'
    SHORTCUT_BREAKREM = 'Ctrl+Shift+B'
    SHORTCUT_CONTINUE = 'F5'
    SHORTCUT_STEPOVER = 'F10'
    SHORTCUT_STEPINTO = 'F11'
    SHORTCUT_STEPOUT = 'Shift+F11'
    SHORTCUT_CODEVIEW = 'Ctrl+L'
    SHORTCUT_ASMVIEW = 'Ctrl+Shift+L'
    
    def __init__(self, title="application"):
        dpg.create_context()
        self.appTitle = title

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
                dpg.add_menu_item(label="GDB Configuration", shortcut=self.SHORTCUT_GDBCONFIG)
                
            with dpg.menu(label="Debug"):
                dpg.add_menu_item(label="Add Breakpoint", shortcut=self.SHORTCUT_BREAKADD)
                dpg.add_menu_item(label="Remove Breakpoint", shortcut=self.SHORTCUT_BREAKREM)
                dpg.add_menu_item(label="Continue execution", shortcut=self.SHORTCUT_CONTINUE)
                dpg.add_menu_item(label="Step over", shortcut=self.SHORTCUT_STEPOVER)
                dpg.add_menu_item(label="Step into", shortcut=self.SHORTCUT_STEPINTO)
                dpg.add_menu_item(label="Step out", shortcut=self.SHORTCUT_STEPOUT)
        
        with self.codeWindow:
            with dpg.menu_bar():
                with dpg.menu(label="View"):
                    dpg.add_menu_item(label="View code", shortcut=self.SHORTCUT_CODEVIEW)
                    dpg.add_menu_item(label="View disassembly", shortcut=self.SHORTCUT_ASMVIEW)
            dpg.add_text("Source code and/or disassembly")
            
        with self.cpuWindow:
            dpg.add_text("CPU registers")
            
        with self.stackWindow:
            dpg.add_text("Stack view")
            
        with self.symWindow:
            dpg.add_text("Variables")
            
        with self.memWindow:
            dpg.add_text("Memory")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        self.busy: bool = True
        
    def run(self):
        while dpg.is_dearpygui_running():
            # do anything here
            dpg.render_dearpygui_frame()

        dpg.destroy_context()
