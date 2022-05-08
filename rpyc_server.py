import rpyc
from rpyc.utils.server import ThreadedServer
import datetime
date_time=datetime.datetime.now()

import _thread
import time
import random
from collections import Counter
import sys

processes = []

class Process:
    def __init__(self, id, role, state):
        self.id = id
        self.role = role
        self.state = state
        self.data = ''
        self.values = []

    # starts a thread that runs the process
    def start(self):
        _thread.start_new_thread(self.run, ())

    def run(self):
        while True:
            time.sleep(5)
            
    def primary_send(self):
        if self.role == 'primary':
            if self.state == 'NF':
                for p in processes:
                    if p.id != self.id:
                        p.data = self.data
            elif self.state == 'F':
                for p in processes:
                    if p.id != self.id:
                        p.data = random.choice(['attack', 'retreat'])
            
    def send_data(self):
        if self.state == 'NF':
            for p in processes:
                if p.id != self.id:
                    p.values.append(self.data)
        elif self.state == 'F':
            for p in processes:
                if p.id != self.id:
                    p.values.append(random.choice(['attack', 'retreat']))
                    
    def quorum(self):
##        if self.values.count('attack') == self.values.count('retreat'):
##            result = 'undefined'
##        else:
        count = Counter(self.values)
        result = count.most_common(1)[0][0]
        return result

def tick(running, processes):
    # program ticks every second
    while running:
        time.sleep(1)

def list(processes):
    for p in processes:
        print("G%s, %s, state=%s" % (p.id, p.role, p.state), end='\n')

def set_state(processes, id, state):
    if state == 'faulty':
        state = 'F'
    elif state == 'non-faulty':
        state = 'NF'
    for p in processes:
        if p.id == id:
            p.state = state
        
def kill(processes, id):
    for p in processes:
        if p.id == id:
            if p.role != 'primary':
                processes.remove(p)
            else:
                processes.remove(p)
                processes[0].role = 'primary'
                
def add(processes, k):
    next_id = processes[-1].id + 1
    for i in range(next_id, next_id + k):
        processes.append(Process(i, 'secondary', 'NF'))
                
def actual_order(processes, order):
    results = []
    faulty = 0
    for p in processes:
        if p.role == 'primary':
            p.data = order
            p.primary_send()
        p.values.clear()
    for p in processes:
        p.values.append(p.data)
        p.send_data()
        if p.state == 'F':
            faulty += 1
    for p in processes:
        results.append(p.quorum())
        print("G%s, %s, majority=%s, state=%s" % (p.id, p.role, p.quorum(), p.state), end='\n')
    
    if len(results) < 4:
        if faulty > 0:
            print("Execute order: cannot be determined – not enough generals in the system! %s faulty nodes in the system" % (faulty), end='\n')
        else:
            print("Execute order: cannot be determined – not enough generals in the system! Non-faulty nodes in the system", end='\n')
    elif results.count('attack') < results.count('retreat'):
        if faulty > 0:
            print("Execute order: retreat! %s faulty nodes in the system – %s out of %s quorum suggest retreat" % (faulty, len(results)//2+1, len(results)), end='\n')
        else:
            print("Execute order: retreat! Non-faulty nodes in the system – %s out of %s quorum suggest retreat" % (len(results)//2+1, len(results)), end='\n')
    elif results.count('attack') > results.count('retreat'):
        if faulty > 0:
            print("Execute order: attack! %s faulty nodes in the system – %s out of %s quorum suggest attack" % (faulty, len(results)//2+1, len(results)), end='\n')
        else:
            print("Execute order: attack! Non-faulty nodes in the system – %s out of %s quorum suggest attack" % (len(results)//2+1, len(results)), end='\n')
            
def parse_lines(lines):
    # utility method to parse input
    result = []
    for l in lines:
        p = l.split(",")
        id = int(p[0].strip())
        name = p[1].strip().split("_")[0]
        time = p[2].strip(" apm").split(":")
        h = int(time[0])
        m = int(time[1])
        s = 0
        t = datetime.time(h, m, s)
        result.append([id, name, t])
    return result

class MonitorService(rpyc.Service):
    def on_connect(self,conn):
        print("\nconnected on {}".format(date_time))
        
        if len(sys.argv) == 2:
            n = sys.argv[1]
            n = int(n)
        else:
            n = 4
        processes.append(Process(1, 'primary', 'NF'))
        for i in range(2, n+1):
            processes.append(Process(i, 'secondary', 'NF'))
        # start threads of all processes
        for p in processes:
            p.start()
        # start the main loop
        running = True
        # start a separate thread for system tick
        _thread.start_new_thread(tick, (running, processes))
        
        global system_start
        system_start = datetime.datetime.now()
        
    def exposed_get_thread_count(self):
        return len(processes)
        
    def exposed_input_cmd(self, cmd):
        print("Recieved command from client: " + cmd)
        inp = cmd.lower()
        cmd = inp.split(" ")

        command = cmd[0]

        if len(cmd) > 3:
            print("Too many arguments")

        # handle exit
        elif command == "exit":
            running = False

        elif len(cmd) == 1 and command == "g-state":
            try:
                list(processes)
            except:
                print("Error")

        elif len(cmd) == 3 and cmd[0] == "g-state":
            try:
                set_state(processes, int(cmd[1]), cmd[2])
                list(processes)
            except:
                print("Error")
        
        elif len(cmd) == 2 and cmd[0] == "g-kill":
            try:
                kill(processes, int(cmd[1]))
                list(processes)
            except:
                print("Error")
        
        elif len(cmd) == 2 and cmd[0] == "g-add":
            try:
                add(processes, int(cmd[1]))
                list(processes)
            except:
                print("Error")
        
        elif len(cmd) == 2 and cmd[0] == "actual-order":
            #try:
            actual_order(processes, cmd[1])
            #except:
                #print("Error")

        # handle unsupported command        
        else:
            print("Unsupported command:", inp)
 
    def on_disconnect(self,conn):
        del processes[:]
        print("Program exited")
        print("disconnected on {}\n".format(date_time))

 
if __name__=='__main__':
 
    t=ThreadedServer(MonitorService, port=18812)
    t.start()