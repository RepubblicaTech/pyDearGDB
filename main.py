from backend.gdbmi import GdbChannel
from wrappers.code import symbols
from wrappers.memory import memory
from wrappers.cpu import cpu

import argparse, sys, os
from pprint import pprint

def clearscreen():
    os.system("cls" if os.name == "nt" else "clear")

# CLI arguments
ourParser = argparse.ArgumentParser(prog=sys.argv[0], description="A custom GDB TUI made in Python")

ourParser.add_argument("-x", "--gdb-script", metavar="/path/to/script.gdb", type=str, nargs=1, help="Path to a GDB script", required=False)
ourParser.add_argument("executable", metavar="/path/to/executable", type=str, nargs=1, help="Path to executable to debug.")

parsedArgs = ourParser.parse_args()

gdbParams: list[str] = [parsedArgs.executable[0]]
if (parsedArgs.gdb_script[0]):
    gdbParams.extend(["-x", parsedArgs.gdb_script[0]])

gdbChannel = GdbChannel(gdbParams)

clearscreen()
while True:
    bp = input("Please insert a function or *address to stop: ")
    if (bp):
        break

gdbCodeManager = symbols.CodeManager(gdbChannel)
gdbMemManager = memory.MemoryManager(gdbChannel)
gdbCPUManager = cpu.CPUManager(gdbChannel)

gdbCodeManager.setBreakpoint(bp)
gdbCodeManager.continueExecution()
clearscreen()
pprint(gdbMemManager.readMemory("0xffffffff80000000", 0, 8))
pprint(gdbCPUManager.viewRegisterValues())

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Quitting...")
    gdbChannel.quit()
