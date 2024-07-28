import argparse
import asyncio
import json
import random

import gi
import websockets

gi.require_version('Gst', '1.0')
from gi.repository import Gst

gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC

gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp


# PIPELINE_DESC = '''
# ximagesrc display-name=:44 ! video/x-raw,framerate=30/1 ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay ! webrtcbin bundle-policy=max-bundle name=sendrecv 
# '''

class WebRTCClient:
    def __init__(self, pipieline_desc):
        self.conn = None
        self.pipe = None
        self.webrtc = None
        self.clientId = None
        self.server = 'ws://localhost:7000'
        self.making_offer = False
        self.ignore_offer = False
        self.is_setting_remote_answer_pending = False
        self.pipeline_desc = pipieline_desc
        self.polite = True
        self.clients = {}

    async def connect(self):

        self.conn = await websockets.connect(self.server)
        await self.conn.send(json.dumps({
            'event': "join-room",
            'room': "room1"
        }))

    def send_sdp_offer(self, offer):
        text = offer.sdp.as_text()
        # msg = json.dumps({'sdp': {'type': 'offer', 'sdp': text}})
        msg = json.dumps({
            "event": "offer",
            "room": "room1",
            "from": "bot",
            "to": self.clientId,
            "description": {
                'type': 'offer',
                'sdp': text
            }
        })
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.conn.send(msg))
        self.making_offer = False

    def on_offer_created(self, promise, _, __):
        promise.wait()
        reply = promise.get_reply()
        offer = reply.get_value('offer')
        promise = Gst.Promise.new()
        self.making_offer = True
        self.webrtc.emit('set-local-description', offer, promise)
        promise.interrupt()
        self.send_sdp_offer(offer)

    def on_negotiation_needed(self, element):
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, element, None)
        element.emit('create-offer', None, promise)

    def send_ice_candidate_message(self, _, mlineindex, candidate):
        icemsg = json.dumps({
            "event": "candidate",
            "candidate": {'candidate': candidate, 'sdpMLineIndex': mlineindex},
            "room": "room1",
            "from": "bot",
            "to": self.clientId
        })
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.conn.send(icemsg))

    def start_pipeline(self):
        self.pipe = Gst.parse_launch(self.pipeline_desc)
        self.webrtc = self.pipe.get_by_name('sendrecv')
        self.webrtc.connect('on-negotiation-needed', self.on_negotiation_needed)
        self.webrtc.connect('on-ice-candidate', self.send_ice_candidate_message)
        self.webrtc.set_property("stun-server", "stun://stun.relay.metered.ca:80")
        self.webrtc.emit('add-turn-server',
                         "turn://2678fb1e408695c7901c6d48:z0t6BANE1JdAAXQm@global.relay.metered.ca:80")
        self.webrtc.emit('add-turn-server',
                         "turn://2678fb1e408695c7901c6d48:z0t6BANE1JdAAXQm@global.relay.metered.ca:443")
        self.pipe.set_state(Gst.State.PLAYING)

    async def handle_sdp(self, message):
        assert (self.webrtc)
        msg = json.loads(message)
        if 'description' in msg:
            sdp = msg['description']
            assert (sdp['type'] == 'answer')
            sdp = sdp['sdp']
            res, sdpmsg = GstSdp.SDPMessage.new()
            GstSdp.sdp_message_parse_buffer(bytes(sdp.encode()), sdpmsg)
            answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
            promise = Gst.Promise.new()
            self.webrtc.emit('set-remote-description', answer, promise)
            promise.interrupt()
        elif 'candidate' in msg:
            ice = msg['candidate']
            if ice:
                candidate = ice['candidate']
                sdpmlineindex = ice['sdpMLineIndex']
                self.webrtc.emit('add-ice-candidate', sdpmlineindex, candidate)

    async def loop(self):
        assert self.conn
        self.connect()
        async for message in self.conn:
            msg: dict = json.loads(message)
            event = msg["event"]
            to = msg["to"] if "to" in msg.keys() else ""
            fromMsg = msg["from"] if "from" in msg.keys() else ""

            if to != "bot":
                continue
            if event == "livestream":
                print('started pipeline')
                self.clientId = fromMsg
                self.start_pipeline()
            else:
                print("need to handle sdp")
                await self.handle_sdp(message)
        return 0


if __name__ == '__main__':
    Gst.init(None)
    parser = argparse.ArgumentParser()
    # parser.add_argument('peerid', help='String ID of the peer to connect to')
    parser.add_argument('--display_num', help='Display number to run gstreamer in ')
    parser.add_argument('--startx', type=str, required=False, )
    parser.add_argument('--starty', type=str, required=False, )
    parser.add_argument('--endx', type=str, required=False, )
    parser.add_argument('--endy', type=str, required=False, )
    args = parser.parse_args()
    our_id = random.randrange(10, 10000)
    # c = WebRTCClient(our_id, args.peerid, args.server)

    pipeline_desc = f"ximagesrc show-pointer=false display-name={args.display_num} startx={args.startx} starty={args.starty} endx={args.endx} endy={args.endy} ! video/x-raw,framerate=30/1 ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay ! webrtcbin bundle-policy=max-bundle name=sendrecv"
    # pipeline_desc = f"videotestsrc ! video/x-raw,framerate=30/1 ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay ! webrtcbin bundle-policy=max-bundle name=sendrecv"
    print(args.display_num)

    c = WebRTCClient(pipeline_desc)
    asyncio.get_event_loop().run_until_complete(c.connect())
    res = asyncio.get_event_loop().run_until_complete(c.loop())
