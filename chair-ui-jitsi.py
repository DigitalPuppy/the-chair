#! /usr/bin/env python3


import wx
import asyncio
import threading
import websockets
import random
import time
import sys
import xml.etree.ElementTree as ET

from chair import Chair

def hex8():
    hx=list(map(lambda x: ord('0')+x, range(0,10))) + list(map(lambda x: ord('a')+x, range(0, 6)))
    v=''
    for i in range(8):
        v += chr(hx[random.randint(0,15)])
    return v
def debug(s):
    print(s, file=sys.stderr)
    return


def comm_thread(frame, room):
    asyncio.run(comm_loop(frame, room))
    
async def comm_loop(frame, room):
    domain='meet.jit.si'
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
        frame.ws = websocket
        fut = None
        while (True):
            if fut is None:
                fut = asyncio.create_task(websocket.recv())
            if len(frame.sending) != 0:
                ts = frame.sending.pop()
                await websocket.send('<message to="'+room+'@'+chatdomain+'" type="groupchat" xmlns="jabber:client"><body>'+ts+'</body></message>')
            if fut.done():
                fut = None
            await asyncio.sleep(0.01)

class MyFrame(wx.Frame):
    def __init__(self):
        self.ws = None
        self.sending = list()
        self.chair = None
        super().__init__(parent=None, title='Control')
        panel = wx.Panel(self)        
        my_sizer = wx.BoxSizer(wx.VERTICAL)        
        self.text_ctrl = wx.TextCtrl(panel)
        my_sizer.Add(self.text_ctrl, 0, wx.ALL | wx.EXPAND, 5)        
        my_btn = wx.Button(panel, label='Connect room')
        my_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        my_sizer.Add(my_btn, 0, wx.ALL | wx.CENTER, 5)

        self.cb_cuff = wx.CheckBox(panel, label='cuff')
        self.cb_cuff.Bind(wx.EVT_CHECKBOX, self.on_cuff)
        my_sizer.Add(self.cb_cuff, 0, wx.ALL | wx.CENTER, 5)

        ssz = wx.BoxSizer(wx.HORIZONTAL)
        self.cb_wand = wx.CheckBox(panel, label='wand')
        self.cb_wand.Bind(wx.EVT_CHECKBOX, self.on_wand)
        ssz.Add(self.cb_wand, 0, wx.ALL | wx.CENTER, 5)
        btn = wx.Button(panel, label='+')
        btn.Bind(wx.EVT_BUTTON, self.on_wand_plus)
        ssz.Add(btn, 0, wx.ALL | wx.CENTER, 5)
        btn = wx.Button(panel, label='-')
        btn.Bind(wx.EVT_BUTTON, self.on_wand_minus)
        ssz.Add(btn, 0, wx.ALL | wx.CENTER, 5)
        my_sizer.Add(ssz)

        ssz = wx.BoxSizer(wx.HORIZONTAL)
        self.cb_elec = wx.CheckBox(panel, label='elec')
        self.cb_elec.Bind(wx.EVT_CHECKBOX, self.on_elec)
        ssz.Add(self.cb_elec, 0, wx.ALL | wx.CENTER, 5)
        my_sizer.Add(ssz, 0, wx.ALL | wx.EXPAND, 5)
        sld = wx.Slider(panel, value = 50, minValue = 0, maxValue = 100, style = wx.SL_HORIZONTAL|wx.SL_LABELS) 
        sld.Bind(wx.EVT_SLIDER, self.on_slider_speed)
        my_sizer.Add(sld, 0, wx.ALL | wx.EXPAND, 5)
        sld = wx.Slider(panel, value = 0, minValue = 0, maxValue = 255, style = wx.SL_HORIZONTAL|wx.SL_LABELS) 
        sld.Bind(wx.EVT_SLIDER, self.on_slider_la)
        my_sizer.Add(sld, 0, wx.ALL | wx.EXPAND, 5)
        sld = wx.Slider(panel, value = 0, minValue = 0, maxValue = 255, style = wx.SL_HORIZONTAL|wx.SL_LABELS) 
        sld.Bind(wx.EVT_SLIDER, self.on_slider_lb)
        my_sizer.Add(sld, 0, wx.ALL | wx.EXPAND, 5)

        lblList = ['waves', 'stroke', 'climb', 'combo', 'intense', 'orgasm'] 
        self.rbox = wx.RadioBox(panel, label = 'RadioBox', choices = lblList, majorDimension = 1, style = wx.RA_SPECIFY_ROWS)
        self.rbox.Bind(wx.EVT_RADIOBOX,self.on_e_mode)
        my_sizer.Add(self.rbox, 0, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(my_sizer)
        self.Show()
    def command(self, cmd):
        if self.chair is None:
            self.sending.append('!' + cmd)
        else:
            self.chair.process_command(cmd)
    def on_e_mode(self, e):
        m = self.rbox.GetStringSelection()
        self.command('e m ' + m)
    def on_slider_speed(self, e):
        val = e.GetEventObject().GetValue()
        self.command("e s " + str(val))
    def on_slider_la(self, e):
        val = e.GetEventObject().GetValue()
        self.command("e a " + str(val))
    def on_slider_lb(self, e):
        val = e.GetEventObject().GetValue()
        self.command("e b " + str(val))
    def on_elec(self, e):
        ison = self.cb_elec.GetValue()
        if ison:
            self.command("e l 1")
        else:
            self.command("e l 0")
    def on_wand(self, e):
        ison = self.cb_wand.GetValue()
        if ison:
            self.command('w on')
        else:
            self.command('w off')
    def on_wand_plus(self, e):
        self.command('w +')
    def on_wand_minus(self, e):
        self.command('w -')
    def on_cuff(self, e):
        ison = self.cb_cuff.GetValue()
        if ison:
            self.command('c c')
        else:
            self.command('c o')
    def on_connect(self, e):
        value = self.text_ctrl.GetValue()
        if len(value) == 0:
            self.chair = Chair(0, '/dev/ttyUSB0', '/dev/ttyACM0')
        else:
            self.comm = threading.Thread(target=comm_thread, args=[self, value])
            self.comm.start()
        
if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()