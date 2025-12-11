from backend.gdbmi import GdbChannel
from wrappers.code import symbols
from wrappers.memory import memory
from wrappers.cpu import cpu

import dearpygui.dearpygui as dpg

class pyGDBApp:
    def __init__(self):
        dpg.create_context()
        self.viewportId = dpg.create_viewport(title="pyGDB Debugger", width=1000, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Enable docking so windows resize automatically
        
        # Main container window that fills the viewport
        with dpg.window(label="Main Layout", width=1000, height=700, no_close=True, no_move=True, no_resize=True):
            with dpg.group(horizontal=True):
                # Left: Code view
                with dpg.child_window(label="Code View", width=500, height=-1, border=True):
                    dpg.add_text("Code / Disassembly")
        
                # Right side
                with dpg.child_window(label="Right Pane", width=-1, height=-1, border=False):
                    # Top half: CPU + Variables side by side
                    with dpg.group(horizontal=True):
                        with dpg.child_window(label="CPU Registers", width=-1, height=300, border=True):
                            dpg.add_text("CPU Registers")
                        with dpg.child_window(label="Variables", width=-1, height=300, border=True):
                            dpg.add_text("Variables")
        
                    # Bottom half: Memory view
                    with dpg.child_window(label="Memory View", width=-1, height=-1, border=True):
                        dpg.add_text("Memory")

    def run(self):
        dpg.start_dearpygui()
        dpg.destroy_context()