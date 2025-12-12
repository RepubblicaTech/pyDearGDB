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
        
        self.codeWindow = dpg.window(label="Code View")
        with self.codeWindow:
            dpg.add_text("Source code + disassembly goes here")
            
        dpg.show_font_manager()

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
