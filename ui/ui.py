from backend.gdbmi import GdbChannel
from wrappers.code import symbols
from wrappers.memory import memory
from wrappers.cpu import cpu

import dearpygui.dearpygui as dpg

class pyGDBApp:
    def __init__(self, title="application"):
        dpg.create_context()
        self.appTitle = title

    def create(self):
        dpg.create_viewport(title='dearGDB', width=1200, height=800)
        
        self.symWindow = dpg.window(label="Variables", width=200, height=400)
        self.stackWindow = dpg.window(label="Stack", pos=(200, 0), width=200, height=400)
        self.codeWindow = dpg.window(label="Code View", pos=(400, 0), width=800, height=500)
        
        self.cpuWindow = dpg.window(label="CPU Registers", pos=(0, 400), width=400, height=400)
        self.memWindow = dpg.window(label="Memory", pos=(400, 500), width=800, height=300)
        
        with self.codeWindow:
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
        
        self.running: bool = True

    def isRunning(self):
        self.running = dpg.is_dearpygui_running()

        return self.running
    
    def render(self):
        dpg.render_dearpygui_frame()
        
    def destroy(self):
        dpg.destroy_context()
