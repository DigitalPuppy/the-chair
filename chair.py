#! /usr/bin/env python3
import sys
import subprocess
import asyncio
import time
from jitsi.jitsichat import hello
import relay_ft245r
import buttshock.et312
from dynamixel_sdk import *

# https://github.com/vpatron/relay_ft245r
class WandRelay:
    """ Setup for a DOXY wand with 3 buttons: on/off + -
        Those remember their level state between turning on and off,
        and pressing - bring them to level 1, not 0.
    """
    def __init__(self, port=0):
        self.maxLevel = 6
        self.currentLevel = 1
        self.is_on = False
        self.R_DOWN = 3
        self.R_UP = 4
        self.R_ON = 2
        self.rb = relay_ft245r.FT245R()
        dev_list = self.rb.list_dev()
        for dev in dev_list:
            print(dev.serial_number, file=sys.stderr)
        self.rb.connect(dev_list[port])
        pass
    def inc(self, val=1):
        self.set_level(self.currentLevel+val)
    def dec(self, val=1):
        self.set_level(self.currentLevel-val)
    def turn_on(self):
        if self.is_on:
            return
        self.pulse(self.R_ON)
        self.is_on = True
    def turn_off(self):
        if not self.is_on:
            return
        self.pulse(self.R_ON)
        self.is_on = False
    def set_level(self, tgt):
        if tgt < 1:
            tgt = 1
        if tgt > self.maxLevel:
            tgt = self.maxLevel
        while tgt < self.currentLevel:
            self.pulse(self.R_DOWN)
            self.currentLevel -= 1
        while tgt > self.currentLevel:
            self.pulse(self.R_UP)
            self.currentLevel += 1
    def pulse(self, relay):
        self.rb.switchon(relay)
        time.sleep(0.3)
        self.rb.switchoff(relay)
        time.sleep(0.3)
        pass
    def get_level(self):
        return (self.is_on, self.currentLevel)

class FakeWandRelay():
    def __init__(self, port=None):
        self.level = 1
        self.is_on = False
    def get_level(self):
        return (self.is_on, self.level)
    def pulse(self, relay):
        print('PULSE ' + str(relay))
    def set_level(self, l):
        self.level = l
    def turn_on(self):
        self.is_on = True
    def turn_off(self):
        self.is_on = False
    def inc(self, val=1):
        pass
    def dec(self, val=1):
        pass

# Constants stolen from arduino version of buttshock
EBOX_MODES = [
    ("waves", 0x76), ('stroke', 0x77), ('climb', 0x78), ('combo', 0x79),
    ('intense', 0x7A), ('orgasm', 0x83)
]
ETMEM_mode = 0x407B
ETMEM_pushbutton = 0x4070
ETBUTTON_setmode = 4
ETBUTTON_lockmode = 16
ETMEM_knobmamin = 0x4086
ETMEM_knobmamax = 0x4087
ETMEM_panellock = 0x400F
ETMEM_knoba = 0x4064
ETMEM_knobb = 0x4065
ETMEM_knobma = 0x4061
ETMEM_knobmaset = 0x420d
class EBox:
    def __init__(self, port):
        self.box = buttshock.et312.ET312SerialSync(port)
        while True: # repeated try forever, with and without saved key
            try:
                self.box.perform_handshake()
                break
            except Exception:
                print('raw handshake failure, retrying...', file=sys.stderr)
                try:
                    with open('et312.key', 'r') as f:
                        k = int(f.read())
                    self.box.key = k
                    self.box.perform_handshake()
                    break
                except Exception:
                    print('keyed handshake failure, retrying...', file=sys.stderr)
                    self.box.key = None
                    time.sleep(0.1)
        print('ebox connected!', file=sys.stderr)
        with open('et312.key', 'w') as f:
            f.write(str(self.box.key))
    def write(self, adr, val):
        self.box.write(adr, [val])
    def set_mode(self, m):
        self.write(ETMEM_mode, m-1)
        self.write(ETMEM_pushbutton, ETBUTTON_setmode)
        time.sleep(0.180);
        self.write(ETMEM_pushbutton, ETBUTTON_lockmode);
        time.sleep(0.180);
    def command(self, cmd):
        """ Do something, always return a one-line string
        """
        try:
            ca = cmd.split(' ')
            w = ca[0]
            char = w[0]
            if char == 'm':
                im = ca[1]
                for em in EBOX_MODES:
                    if len(im) <= len(em[0]) and em[0][0:len(im)] == im:
                        self.set_mode(em[1])
                        return "mode set to " + em[0]
                return "unknown mode " + im
            if char == 's':
                v = int(ca[1])
                minv = self.box.read(ETMEM_knobmamin)
                maxv = self.box.read(ETMEM_knobmamax)
                tgt = (100-v) * (maxv-minv) // 100 + minv
                if tgt < minv:
                    tgt = minv
                if tgt > maxv:
                    tgt = maxv
                self.write(ETMEM_knobmaset, tgt)
                return 'speed set to ' + str(v) + '(' + str(tgt) + ')'
            if char == 'a':
                v = int(ca[1])
                self.write(ETMEM_knoba, v)
                return 'a channel set to ' + str(v)
            if char == 'b':
                v = int(ca[1])
                self.write(ETMEM_knobb, v)
                return 'b channel set to ' + str(v)
            if char == 'l':
                v = int(ca[1])
                self.write(ETMEM_panellock, v)
                return 'lock set to ' + str(v)
            if char == 'h':
                return 'speed(0-100),a|b(0-255),lock(0-1),mode(waves,stroke,climob,combo,intense,orgasm)'
            return 'unknown command, h for help'
        except Exception as e:
            print(e, file=sys.stderr)
            return 'exception processing command'
class FakeEBox():
    def __init__(self, port=None):
        pass
    def command(self, cmd):
        print('E: ' + cmd)
class EBoxBridge:
    def __init__(self, port):
        self.p = subprocess.Popen(['./bzt/bzt', str(port)],
            stdout = subprocess.PIPE,
            stdin = subprocess.PIPE
            )
    def forward_command(self, cmd):
        self.p.stdin.write(cmd + '\n')
        return self.p.stdout.readline()

ADDR_MX_TORQUE_ENABLE      = 24               # Control table address is different in Dynamixel model
ADDR_MX_GOAL_POSITION      = 30
ADDR_MX_PRESENT_POSITION   = 132
DXL_BROADCAST_ID = 254

class CuffControl:
    def __init__(self, port):
        self.OPEN_POS = 205
        self.CLOSE_POS = 819
        self.portHandler = PortHandler(port)
        self.packetHandler = PacketHandler(1.0)
        if not self.portHandler.openPort():
            raise Exception("cannot open port")
        if not self.portHandler.setBaudRate(1000000):
            raise Exception("cannot set baud rate")
        self.set_torque()
        self.switch_open()
    def set_torque(self):
        self.packetHandler.write1ByteTxRx(self.portHandler, DXL_BROADCAST_ID, ADDR_MX_TORQUE_ENABLE, 1)
    def switch_close(self):
        self.packetHandler.write2ByteTxRx(self.portHandler, DXL_BROADCAST_ID, ADDR_MX_GOAL_POSITION, self.CLOSE_POS)
    def switch_open(self):
        self.packetHandler.write2ByteTxRx(self.portHandler, DXL_BROADCAST_ID, ADDR_MX_GOAL_POSITION, self.OPEN_POS)

class FakeCuffControl():
    def __init__(self, port = None):
        pass
    def set_torque(self):
        print('torque on')
    def switch_close(self):
        print('close')
    def switch_open(self):
        print('open')

class Chair:
    def __init__(self, wport, eport, cport):
        self.wand = wport == 'fake' and FakeWandRelay() or WandRelay(int(wport))
        self.electro = eport == 'fake' and FakeEBox() or EBox(eport)
        self.cuff = cport == 'fake' and FakeCuffControl() or CuffControl(cport)
    def finish(self):
        self.cuff.switch_open()
        self.electro.command("lock 0")
        self.wand.turn_off()
    def do_process_command(self, cmdstr):
        cmda = cmdstr.split(' ')
        cmd = cmda[0]
        cmdc = cmd[0]
        if cmdc == 'w':
            payload = cmda[1]
            if payload[0] == '+':
                self.wand.inc(len(payload))
            elif payload[0] == '-':
                self.wand.dec(len(payload))
            elif payload == 'on':
                self.wand.turn_on()
            elif payload == 'off' or payload == '0':
                self.wand.turn_off()
            elif payload == 'forcelow':
                self.wand.pulse(self.wand.R_DOWN)
            elif payload == 'forcehi':
                self.wand.pulse(self.wand.R_UP)
            else:
                self.wand.set_level(int(payload))
            s, l = self.wand.get_level()
            return "wand set to state " + (s and 'on' or 'off') + " level " + str(l)
        elif cmdc == 'c':
            payload = cmda[1][0]
            if payload == 'c' or payload == '1':
                self.cuff.switch_close()
                return "cuff closed"
            else:
                self.cuff.switch_open()
                return "cuff opened"
        elif cmdc == 'e':
            return self.electro.command(' '.join(cmda[1:]))
        elif cmdc == 'h':
            return "commands: c close|open,  w +|-|level|on|off, e help|mode|knoba|knobb|speed value"
    def process_command(self, cmdstr):
        print('!' + cmdstr, file=sys.stderr)
        try:
            return self.do_process_command(cmdstr)
        except Exception as e:
            print('bronk ' + str(e), file=sys.stderr)
            return "ERROR: " + str(e)

if __name__ == '__main__':
    c = Chair(*sys.argv[1:4])
    while True:
        l = sys.stdin.readline().strip()
        r = c.process_command(l)
        print(r)

if False and __name__ == '__main__':
    e = EBox(sys.argv[1])
    while True:
        l = sys.stdin.readline().strip()
        r = e.command(l)
        print(r)

if False and __name__ == '__main__':
    w = WandRelay()
    while True:
        l = sys.stdin.readline().strip()
        if l[0] == 'u':
            w.rb.switchon(int(l[1]))
        elif l[0] == 'd':
            w.rb.switchoff(int(l[1]))
        elif l[0] == '+':
            w.inc(len(l))
        elif l[0] == '-':
            w.dec(len(l))
        elif l == 'on':
            w.turn_on()
        elif l == 'off' or l == '0':
            w.turn_off()
        else:
            w.set_level(int(l))