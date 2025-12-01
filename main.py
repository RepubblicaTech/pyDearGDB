from backend.gdbmi import GdbChannel
from wrappers.code import symbols
import argparse, sys

# CLI arguments
ourParser = argparse.ArgumentParser(prog=sys.argv[0], description="A custom GDB TUI made in Python")

ourParser.add_argument("-x", "--gdb-script", metavar="/path/to/script.gdb", type=str, nargs=1, help="Path to a GDB script", required=False)
ourParser.add_argument("executable", metavar="/path/to/executable", type=str, nargs=1, help="Path to executable to debug.")

parsedArgs = ourParser.parse_args()

gdbParams: list[str] = [parsedArgs.executable[0]]
if (parsedArgs.gdb_script[0]):
    gdbParams.extend(["-x", parsedArgs.gdb_script[0]])

gdbChannel = GdbChannel(gdbParams)
gdbCodeManager = symbols.CodeManager(gdbChannel)

# Example: send a command

print(gdbCodeManager.setBreakpoint("kstart"))
print(gdbCodeManager.continueExecution())

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Quitting...")
    gdbChannel.quit()