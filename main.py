from backend.gdbmi import gdbPipe
import argparse, sys

# CLI arguments
ourParser = argparse.ArgumentParser(prog=sys.argv[0], description="A custom GDB TUI made in Python")

ourParser.add_argument("-x", "--gdb-script", metavar="/path/to/script.gdb", type=str, nargs=1, help="Path to a GDB script", required=False)
ourParser.add_argument("executable", metavar="/path/to/executable", type=str, nargs=1, help="Path to executable to debug.")

parsedArgs = ourParser.parse_args()

gdbParams: list[str] = [parsedArgs.executable[0]]
if (parsedArgs.gdb_script[0]):
    gdbParams.extend(["-x", parsedArgs.gdb_script[0]])

gdbChannel = gdbPipe(gdbParams)

# Example: send a command

gdbChannel.sendCmd("-break-insert kstart")
gdbChannel.sendCmd("-exec-continue")

#     def wait_for_breakpoint(self):
#         while True:
#             try:
#                 responses = self.gdbmi.get_gdb_response(timeout_sec=0.5)
#             except constants.GdbTimeoutError:
#                 print(".")
#                 continue
#             for r in responses:
#                 if r["type"] == "notify" and r["message"] == "stopped":
#                     if r["payload"].get("reason") == "breakpoint-hit":
#                         return r  # return the breakpoint event
    
# print(gdbChannel.wait_for_breakpoint())

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Quitting...")
    gdbChannel.quit()