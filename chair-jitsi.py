#! /usr/bin/env python3

import sys
import argparse
import asyncio
import signal
import threading

from chair import Chair
import jitsi.jitsichat

parser = argparse.ArgumentParser(
                    prog = 'chair-jitsi',
                    description = 'Control The Chair through jitsi chat',
                    epilog = 'Enjoy')
parser.add_argument('--port-elec', '-e')
parser.add_argument('--port-relay', '-w')
parser.add_argument('--port-motor', '-m')
parser.add_argument('--jitsi-domain', '-d')
parser.add_argument('--jitsi-room', '-r')
parser.add_argument('--stop-after', '-s')
args = parser.parse_args()

chair = Chair(int(args.port_relay), args.port_elec, args.port_motor)

def abort(sn, bt):
    print('got signal, stopping')
    chair.finish()
    sys.exit(0)

async def auto_stop(delay):
    await asyncio.sleep(delay)
    print('stopping after delay')
    chair.finish()
    sys.exit(0)

signal.signal(signal.SIGUSR1, abort)
signal.signal(signal.SIGTERM, abort)
#signal.signal(signal.SIGKILL, abort)

async def async_stdin():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    return reader

async def stop_on_stdin():
    reader = await async_stdin()
    await reader.read(1)
    print('stopping on stdin')
    chair.finish()
    sys.exit(0)

async def handle_input(data):
    if data[0] != '!':
        return
    return chair.process_command(data[1:])
def safety1():
    print('Hit return to shutdown')
    sys.stdin.read(1)
    #getch.getch()
    chair.finish()
    sys.exit(1)
t1 = threading.Thread(target=safety1)
t1.start()
if args.stop_after is not None:
    asyncio.create_task(auto_stop(int(args.stop_after)))
#asyncio.create_task(stop_on_stdin())
asyncio.run(jitsi.jitsichat.hello(handle_input,
    domain=(args.jitsi_domain or 'meet.jit.si'),
    room=args.jitsi_room))