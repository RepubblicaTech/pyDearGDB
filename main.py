import subprocess

gdb = subprocess.Popen(
    ["gdb", "--interpreter=mi2", "-x", "debug_iso.gdb", "build/kernel.elf"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Example: send a command
gdb.stdin.write("-break-insert kstart\n")
gdb.stdin.flush()
gdb.stdin.write("-exec-continue\n")
gdb.stdin.flush()

# Read structured output
while True:
    line = gdb.stdout.readline()
    # print("GDB:", line.strip())
