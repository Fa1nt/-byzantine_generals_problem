import rpyc
import sys
 
if len(sys.argv) < 2:
    exit("Usage {} SERVER".format(sys.argv[0]))
 
server = sys.argv[1]

conn = rpyc.connect(server,18812)

while True:
    threads = conn.root.get_thread_count()
    if conn.root.get_thread_count() != 0:
        print("The number of generals created: " + str(threads))
        break

while True:
    cmd = input("Input the command: ")
    conn.root.input_cmd(cmd)
    if cmd.lower() == "exit":
        break