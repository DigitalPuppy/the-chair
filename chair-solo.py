#! /usr/bin/env python3
import sys
import threading
import time
import random
import signal
#not working, blocks all threads import getch
from chair import Chair

# CONFIG
e_modes = ('waves', 'stroke', 'climb', 'combo', 'orgasm')
e_mode_reroll = ((30, 90),)
e_levels_a = ((100,140), (140, 180), (180, 210), (210, 255))
e_levels_b = ((100,140), (140, 180), (180, 210), (210, 255))
e_level_reroll = ((5, 20),)
w_level = (0, 2, 4, 6)
w_shift = (True,)
w_shift_reroll = (10,)
phase_duration = (30, 50, 50)

def conf_at_phase(entry, phase):
    if len(entry) > phase:
        return entry[phase]
    return entry[len(entry)-1]
def roll(rang):
    return random.randrange(rang[0], rang[1])

# check
int(sys.argv[1])

class FakeChair():
    def __init__(self, a, b, c):
        pass
    def process_command(self, cmd):
        print(cmd)
    def finish(self):
        print('FINISH')

c = Chair(*sys.argv[2:5])
finished = False
def abort(sn, bt):
    print('got signal, stopping')
    finish()
def finish():
    global finished
    c.finish()
    finished = True
    sys.exit(0)
def safety1():
    print('Will shutdown in ' + sys.argv[1] + ' seconds')
    time.sleep(int(sys.argv[1]))
    finish()
def safety2():
    print('Hit return to shutdown')
    sys.stdin.read(1)
    #getch.getch()
    finish()
t1 = threading.Thread(target=safety1)
t1.start()
t2 = threading.Thread(target=safety2)
t2.start()
signal.signal(signal.SIGUSR1, abort)
signal.signal(signal.SIGTERM, abort)
#signal.signal(signal.SIGKILL, abort)

# start sequence
c.process_command('w on')
remain=10
while remain > 0:
    print(str(remain) + '...')
    time.sleep(1)
    c.process_command("w forcelow")
    remain -= 1
c.process_command('w off')
c.process_command('c close')
c.process_command('e lock 1')
cphase = 0
cphasetick = 0
enextmroll = 0
enextlroll = 0
while not finished:
    if enextmroll <= cphasetick:
        m = e_modes[random.randrange(len(e_modes))]
        enextmroll = cphasetick + 1 + roll(conf_at_phase(e_mode_reroll, cphase))
        c.process_command('e m ' + m)
    if enextlroll <= cphasetick:
        la = roll(conf_at_phase(e_levels_a, cphase))
        lb = roll(conf_at_phase(e_levels_b, cphase))
        enextlroll = cphasetick + 1 + roll(conf_at_phase(e_level_reroll, cphase))
        c.process_command('e a ' + str(la))
        c.process_command('e b ' + str(lb))
    cphasetick+=1
    print('tick ' + str(cphasetick), file=sys.stderr)
    if len(phase_duration) > cphase and cphasetick >= phase_duration[cphase]:
        print('end phase ' + str(cphase), file=sys.stderr)
        cphase += 1
        enextmroll = 0
        enextlroll = 0
        cphasetick = 0
        c.process_command('w ' + str(w_level[cphase]))
        if w_level[cphase] != 0:
            c.process_command('w on')
        else:
            c.process_command('w off')
    time.sleep(1)