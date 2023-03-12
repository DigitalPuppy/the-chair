#! /usr/bin/env python3

import sys
import os
import time
import asyncio
import websockets
import random
import xml.etree.ElementTree as ET

def hex8():
    hx=list(map(lambda x: ord('0')+x, range(0,10))) + list(map(lambda x: ord('a')+x, range(0, 6)))
    v=''
    for i in range(8):
        v += chr(hx[random.randint(0,15)])
    return v

#print(hex8())
#print(hex8())
def debug(s):
    print(s, file=sys.stderr)
    return

async def dumpit(txt):
    print("TEXT: " + txt)

async def hello(processor, domain='meet.jit.si', chatdomain=None, room='rocketchatundefinedtgpqjthn4xr3dmgnc'):
    if chatdomain is None:
        chatdomain = 'conference.' + domain
    async with websockets.connect("wss://"+domain+"/xmpp-websocket?room=" + room, origin='https://'+domain,subprotocols=['xmpp']) as websocket:
        await websocket.send('<open to="'+domain+'" version="1.0" xmlns="urn:ietf:params:xml:ns:xmpp-framing"/>')
        debug(await websocket.recv())
        debug(await websocket.recv())
        await websocket.send('<auth mechanism="ANONYMOUS" xmlns="urn:ietf:params:xml:ns:xmpp-sasl"/>')
        debug(await websocket.recv())
        await websocket.send('<open to="'+domain+'" version="1.0" xmlns="urn:ietf:params:xml:ns:xmpp-framing"/>')
        debug(await websocket.recv())
        debug(await websocket.recv())
        await websocket.send('<iq id="_bind_auth_2" type="set" xmlns="jabber:client"><bind xmlns="urn:ietf:params:xml:ns:xmpp-bind"/></iq>')
        debug(await websocket.recv())
        debug(await websocket.recv())
        await websocket.send('<iq id="_session_auth_2" type="set" xmlns="jabber:client"><session xmlns="urn:ietf:params:xml:ns:xmpp-session"/></iq>')
        debug(await websocket.recv())
        await websocket.send('<enable resume="true" xmlns="urn:xmpp:sm:3"/>')
        debug(await websocket.recv())
        #                      <presence to="rocketchatundefinedtgpqjthn4xr3dmgnc@conference.meet.jit.si/d71a39e7" xmlns="jabber:client"><x xmlns="http://jabber.org/protocol/muc"/><stats-id>Zora-sXy</stats-id><c hash="sha-1" node="https://jitsi.org/jitsi-meet" ver="zI2SFRd7GspEplY5WO8C4+MeFgQ=" xmlns="http://jabber.org/protocol/caps"/><SourceInfo>{}</SourceInfo><jitsi_participant_region>eu-west-2</jitsi_participant_region><jitsi_participant_codecType>vp8</jitsi_participant_codecType><nick xmlns="http://jabber.org/protocol/nick">canard</nick></presence>
        await websocket.send('<presence to="'+room+'@'+chatdomain+'/'+hex8() + '" xmlns="jabber:client"><x xmlns="http://jabber.org/protocol/muc"/><stats-id>Zora-sXy</stats-id><c hash="sha-1" node="https://jitsi.org/jitsi-meet" ver="zI2SFRd7GspEplY5WO8C4+MeFgQ=" xmlns="http://jabber.org/protocol/caps"/><SourceInfo>{}</SourceInfo><jitsi_participant_region>eu-west-2</jitsi_participant_region><jitsi_participant_codecType>vp8</jitsi_participant_codecType><nick xmlns="http://jabber.org/protocol/nick">leBot</nick></presence>')
        debug(await websocket.recv())
        await websocket.send('<message to="'+room+'@'+chatdomain+'" type="groupchat" xmlns="jabber:client"><body>je suis un bot</body></message>')
        debug(await websocket.recv())
        while (True):
            #await websocket.send('<iq id="ce08bade-75fd-4932-876c-5e6d1274b388:sendIQ" to="meet.jit.si" type="get" xmlns="jabber:client"><ping xmlns="urn:xmpp:ping"/></iq>')
            xml = await websocket.recv()
            data = ET.fromstring(xml)
            debug(xml)
            debug(data.tag)
            if data.tag != '{jabber:client}message':
                continue
            debug(data[0].tag)
            try:
                res = await processor(data[0].text) # assumes body is 0
                if res is not None:
                    await websocket.send('<message to="'+room+'@'+chatdomain+'" type="groupchat" xmlns="jabber:client"><body>'+res+'</body></message>')
            except Exception:
                pass
            #await asyncio.sleep(2)
            # receive: <message type='groupchat' from='rocketchatundefinedtgpqjthn4xr3dmgnc@conference.meet.jit.si/8b160e34' xmlns='jabber:client' to='7ee77055-fcdc-4aca-86b1-0fd36ca87124@meet.jit.si/uRen5xOkZ9M1' xml:lang='en' id='QIm5tqbl6QmefFcuCYLcNjPE'><body>je suis un bot</body><occupant-id xmlns='urn:xmpp:occupant-id:0' id='/yn7zH2APbsCeZjkwes/4XlZXHtZMhqB7sU2WOld50M='/></message>


if __name__ == '__main__':
    asyncio.run(hello(dumpit))
