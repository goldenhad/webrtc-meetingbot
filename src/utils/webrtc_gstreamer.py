import argparse
from time import sleep
import asyncio
import json
import socketio
import threading

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC

gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp


sio = socketio.AsyncClient()

class WebRTCPeerConnection:
    def __init__(self, clientId, pipeline, loop):
        self.clientId = clientId
        self.pipeline = pipeline
        self.loop = loop
        self.create_webrtcbin()

    def create_webrtcbin(self):
        videotee = self.pipeline.get_by_name("videotee")
        audiotee = self.pipeline.get_by_name("audiotee")

        rtp_vid = Gst.ElementFactory.make("rtph264pay",f'rtp_vid-{self.clientId}')
        rtp_aud = Gst.ElementFactory.make("rtpopuspay",f'rtp_aud-{self.clientId}')
        webrtcbin = Gst.ElementFactory.make("webrtcbin",f"sendrecv-{self.clientId}")
        queue_v = Gst.ElementFactory.make("queue",f'q_vid-{self.clientId}')
        queue_a = Gst.ElementFactory.make("queue",f'q_aud-{self.clientId}')

        self.pipeline.add(rtp_vid)
        self.pipeline.add(webrtcbin)
        self.pipeline.add(rtp_aud)
        self.pipeline.add(queue_a)
        self.pipeline.add(queue_v)

        videotee = self.pipeline.get_by_name("videotee")
        videotee.link(queue_v)
        queue_v.link(rtp_vid)
        rtp_vid.set_property("config-interval",-1)
        rtp_vid.link(webrtcbin)

        # # Link audio tee to muxer
        audiotee = self.pipeline.get_by_name("audiotee")
        audiotee.link(queue_a)
        queue_a.link(rtp_aud)
        rtp_aud.link(webrtcbin)

        self.webrtc = self.pipeline.get_by_name(f'sendrecv-{self.clientId}')
        self.webrtc.connect('on-negotiation-needed', self.on_negotiation_needed)
        self.webrtc.connect('on-ice-candidate', self.send_ice_candidate_message)
        # self.webrtc.set_property("ice-transport-policy",1)
        self.webrtc.set_property("stun-server", "stun://stun.relay.metered.ca:80")
        self.webrtc.emit('add-turn-server',
                         "turn://2678fb1e408695c7901c6d48:z0t6BANE1JdAAXQm@global.relay.metered.ca:80")
        self.webrtc.emit('add-turn-server',
                         "turn://2678fb1e408695c7901c6d48:z0t6BANE1JdAAXQm@global.relay.metered.ca:443")

        print("added webrtcbin")
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("ERROR: Unable to set the pipeline to the playing state")

        Gst.debug_bin_to_dot_file(self.pipeline,  Gst.DebugGraphDetails.ALL, "after_webrtcbin_made")

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
            "candidate": {'candidate': candidate, 'sdpMLineIndex': mlineindex},
            "from": "bot", # removed 'room'. handled by socketio automatically
            "to": self.clientId
        })
        asyncio.run_coroutine_threadsafe(sio.emit('candidate',icemsg), self.loop)

    def send_sdp_offer(self, offer):
        text = offer.sdp.as_text()
        msg = json.dumps({
            "from": "bot", # removed 'room' as its handled by socketio automatically
            "to": self.clientId,
            "description": {
                'type': 'offer',
                'sdp': text
            }
        })
        asyncio.run_coroutine_threadsafe(sio.emit('offer',msg), self.loop)
        self.making_offer = False

    async def handle_sdp(self, msg):
        assert self.webrtc
        if 'description' in msg:
            sdp = msg['description']
            assert sdp['type'] == 'answer'
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
class WebRTCClient:
    def __init__(self, pipeline, meeting_id):
        self.pipe = None
        self.webrtc = None
        self.clientId = None
        self.server = 'http://localhost:7000'
        self.making_offer = False
        self.ignore_offer = False
        self.is_setting_remote_answer_pending = False
        self.pipeline = pipeline
        self.peerconnections: list[WebRTCPeerConnection] = []
        self.polite = True
        self.meeting_id = meeting_id
        self.loop = asyncio.get_event_loop()

        @sio.event
        async def connect():
            print("Connected to server from webrtcclient")
            await sio.emit('join-room-for-new-bot', self.meeting_id)

        @sio.event
        async def disconnect():
            print("Disconnected from server")

        @sio.on('*')
        async def any_event(event,data):
            # print("got event from socketio:",end=" ")
            # print(event,json.loads(data))
            print("webrtcclient: ",event)
            if event == "livestream" or event == "offer" or event == "candidate" or event == "answer":
                await self.handle_message(event, data)

    async def connect(self):
        await sio.connect(self.server)

    async def handle_message(self,event, message):
        msg = json.loads(message)
        to = msg.get('to')
        fromMsg = msg.get('from')
        
        webrtcpc = None
        for pc in self.peerconnections:
            if pc.clientId == fromMsg:
                webrtcpc = pc

        if to != "bot":
            return

        if event == "livestream":
            self.clientId = fromMsg
            # self.start_pipeline()
            print("creating webrtcbin")
            self.peerconnections.append(
                WebRTCPeerConnection(self.clientId, self.pipeline, self.loop)
            )
            # self.create_webrtcbin(self.pipeline)
        elif event == "offer" or event == 'answer':
            assert webrtcpc
            await webrtcpc.handle_sdp(msg)
        elif event == "candidate":
            assert webrtcpc
            await webrtcpc.handle_sdp(msg)


    async def run(self):
        await self.connect()
        await self.send_test_msg()
        while True:
            await asyncio.sleep(1)

    async def send_test_msg(self):
        await sio.emit("test",{'from':"Bot"})

def gst_thread_func(pipeline):
    # wait until error, EOS or State-Change
    terminate = False
    bus = pipeline.get_bus()
    while True:
        try:
            msg = bus.timed_pop_filtered(
                0.5 * Gst.SECOND,
                Gst.MessageType.ERROR | Gst.MessageType.EOS | Gst.MessageType.STATE_CHANGED)

            if msg:
                t = msg.type
                if t == Gst.MessageType.ERROR:
                    err, dbg = msg.parse_error()
                    print("ERROR:", msg.src.get_name(), ":", err.message)
                    if dbg:
                        print("Debug information:", dbg)
                    terminate = True
                elif t == Gst.MessageType.EOS:
                    print("End-Of-Stream reached")
                    terminate = True
                elif t == Gst.MessageType.STATE_CHANGED:
                    # we are only interested in state-changed messages from the
                    # pieline
                    if msg.src == pipeline:
                        old, new, pending = msg.parse_state_changed()
                        print(
                            "Pipeline state changed from",
                            Gst.Element.state_get_name(old),
                            "to",
                            Gst.Element.state_get_name(new),
                            ":")

                else:
                    # should not get here
                    print("ERROR: unexpected message received")
        except KeyboardInterrupt:
            terminate = True

        if terminate:
            break
    # GLib.MainLoop().run()


def save_to_file(output_filename, pipe):
    Gst.debug_bin_to_dot_file(pipe,  Gst.DebugGraphDetails.ALL, "before_save_to_file")

    muxer = Gst.ElementFactory.make('avimux', 'muxer')
    filesink = Gst.ElementFactory.make('filesink', 'filesink')
    queue_v = Gst.ElementFactory.make("queue",'q_vid')
    queue_a = Gst.ElementFactory.make("queue",'q_aud')
    filesink.set_property('location', output_filename)
    #
    pipe.add(queue_v)
    pipe.add(queue_a)
    pipe.add(muxer)
    pipe.add(filesink)

    videotee = pipe.get_by_name("videotee")
    videotee.link(queue_v)
    queue_v.link(muxer)

    # # Link audio tee to muxer
    audiotee = pipe.get_by_name("raw_audio")
    audiotee.link(queue_a)
    queue_a.link(muxer)

    muxer.link(filesink)
    print("linked")
    ret = pipe.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("ERROR: Unable to set the pipeline to the playing state")

if __name__ == '__main__':
    Gst.init(None)
    parser = argparse.ArgumentParser()
    parser.add_argument('--display_num', help='Display number to run gstreamer in')
    parser.add_argument('--startx', type=str, required=False)
    parser.add_argument('--starty', type=str, required=False)
    parser.add_argument('--endx', type=str, required=False)
    parser.add_argument('--endy', type=str, required=False)
    parser.add_argument('--meetingId', type=str, required=False)
    args = parser.parse_args()

        # ximagesrc show-pointer=false display-name={args.display_num} startx={args.startx} starty={args.starty} endx={args.endx} endy={args.endy} ! \
    test_pipeline_desc = f'''
        videotestsrc !
        video/x-raw,framerate=30/1,width=1920,height=1080 ! videoconvert ! queue ! \
        x264enc speed-preset=ultrafast tune=zerolatency ! \
        h264parse ! \
        tee name=videotee \
        pulsesrc device=chrome_sink.monitor ! audioconvert !\
        tee name=raw_audio \
        raw_audio. ! audioresample ! \
        queue ! opusenc ! \
        tee name=audiotee \
        audiotee. ! queue ! fakesink\
        videotee. ! queue ! fakesink
    '''

    test_recording_desc = f'''
        videotestsrc ! \
        video/x-raw,framerate=30/1,width=1280,height=720 ! videoconvert !\
        queue ! vp8enc !\
        tee name=videotee
        pulsesrc  !\
        audioconvert ! audioresample \
        ! queue ! opusenc !\
        tee name=audiotee\
        audiotee. ! queue ! fakesink async=false \

    '''

    test_recording_vid_desc = f'''
        videotestsrc ! \
        video/x-raw,framerate=30/1,width=1280,height=720 ! videoconvert !\
        queue ! vp8enc !\
        matroskamux name=m ! filesink location=test.mkv
        pulsesrc  !\
        audioconvert ! audioresample \
        ! queue ! opusenc !\
        m.

    '''


    recording_desc = f'''
        ximagesrc show-pointer=false use-damage=false display-name={args.display_num} startx={args.startx} \
        starty={args.starty} endx={args.endx} endy={args.endy} ! \
        queue !video/x-raw,framerate=30/1! queue ! videoconvert ! queue \
        ! vp8enc deadline=1 ! queue ! webmmux name=mux ! queue ! filesink location=output.webm \
        pulsesrc device=chrome_sink.monitor ! queue ! audioconvert ! queue ! audioresample ! queue ! opusenc ! mux.
    '''

    pipeline_desc = f'''
        ximagesrc show-pointer=false use-damage=false display-name={args.display_num} startx={args.startx} starty={args.starty} endx={args.endx} endy={args.endy} ! \
        video/x-raw,framerate=30/1 ! videoconvert ! queue ! \
        nvh264enc ! \
        h264parse ! \
        tee name=videotee \
        pulsesrc device=chrome_sink.monitor ! audioconvert !\
        tee name=raw_audio \
        raw_audio. ! audioresample ! \
        queue ! opusenc ! \
        tee name=audiotee \
        audiotee. ! queue ! fakesink\
        videotee. ! queue ! fakesink
    '''
    pipe = Gst.parse_launch(pipeline_desc)
    # pipe.set_state(Gst.State.PLAYING)

    loop = asyncio.get_event_loop()
    # c = WebRTCClient(pipeline_desc, args.meetingId)
    c = WebRTCClient(pipe, "b1786fdc-1120-41a5-8f7c-3deebdcdd71f" )

    # gst_thread = threading.Thread(target=gst_thread_func, args=(loop,))
    threading.Thread(target=gst_thread_func, daemon=True, args=(pipe,)).start()
    # gst_thread.start()

    Gst.debug_bin_to_dot_file(pipe,  Gst.DebugGraphDetails.ALL, "initial")
    # Run the asyncio event loop
    # save_to_file('testfile.mkv',pipe)
    # sleep(10)
    save_to_file('output.avi',pipe)
    print("started rec")
    loop.run_until_complete(c.run())
