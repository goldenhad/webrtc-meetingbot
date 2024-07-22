import React, { useEffect, useRef, useState } from 'react';
import { ReadyState } from 'react-use-websocket';
import { useWebSocket } from 'react-use-websocket/dist/lib/use-websocket';

const App = () => {
  const [pc,setPc] = useState(null)
  const [polite,setPolite] = useState(true)
  const [makingoffer,setMakingOffer] = useState(false)
  const [ignoreoffer,setIgnoreOffer] = useState(false)
  const [issettingremoteanswerpending,setIsssettingremoteanswerpending] = useState(false)
  const { readyState,sendJsonMessage} = useWebSocket("ws://127.0.0.1:7000/ws",
    {
      onMessage:
      async ({data}) => {
        const description = JSON.parse(data)?.description
        const candidate = JSON.parse(data)?.candidate
        try {
          if (description) {
            // an offer may come in while we are busy processing srd(answer).
            // in this case, we will be in "stable" by the ime the offer is processed
            // so it is safe to chain it on our operations chain now.
            const readyforoffer =
              !makingoffer &&
              (pc.signalingstate == "stable" || issettingremoteanswerpending);
            const offercollision = description.type == "offer" && !readyforoffer;

            setIgnoreOffer(!polite && offercollision)
            if (ignoreoffer) {
              return;
            }
            setIsssettingremoteanswerpending(description.type == "answer")
            await pc.setRemoteDescription(description); // srd rolls back as needed
            setIsssettingremoteanswerpending(false)
            if (description.type == "offer") {
              await pc.setLocalDescription();
              sendJsonMessage({ event: pc.localDescription.type, room: 'room1',from:"react", description: pc.localDescription })
            }
          } else if (candidate) {
            try {
              await pc.addIceCandidate(candidate);
            } catch (err) {
              if (!ignoreoffer) throw err; // suppress ignored offer's candidates
            }
          }
        } catch (err) {
          console.error(err);
        }   //};
      },
      shouldReconnect: () => true,
       
    }
  )
  useEffect(()=>{
    setPc(new RTCPeerConnection({iceServers: [
      {
        urls: "stun:stun.relay.metered.ca:80",
      },
      {
        urls: "turn:global.relay.metered.ca:80",
        username: "2678fb1e408695c7901c6d48",
        credential: "z0t6BANE1JdAAXQm",
      },
      {
        urls: "turn:global.relay.metered.ca:80?transport=tcp",
        username: "2678fb1e408695c7901c6d48",
        credential: "z0t6BANE1JdAAXQm",
      },
      {
        urls: "turn:global.relay.metered.ca:443",
        username: "2678fb1e408695c7901c6d48",
        credential: "z0t6BANE1JdAAXQm",
      },
      {
        urls: "turns:global.relay.metered.ca:443?transport=tcp",
        username: "2678fb1e408695c7901c6d48",
        credential: "z0t6BANE1JdAAXQm",
      },
  ]}))
  },[])

  useEffect(()=>{
    if (readyState == ReadyState.OPEN) {
      sendJsonMessage({ event: 'join-room', room: 'room1' }) 
    }
    console.log('readystate',readyState)
  },[readyState])

  const makeOffer = async () =>{
        try {
          setMakingOffer(true)
          await pc.setLocalDescription();
          console.log("making offer")
          sendJsonMessage({ event: pc.localDescription.type, room: 'room1',from:"react", description: pc.localDescription })
        } catch (err) {
          console.error(err);
        } finally {
          setMakingOffer(false)
        }

  }

  useEffect(() => {
    if (pc != null) {

      // send any ice candidates to the other peer
      pc.onicecandidate = ({candidate}) => sendJsonMessage({ event: 'candidate', room: 'room1',from:"react", candidate: candidate })  
      //       
      // let the "negotiationneeded" event trigger offer generation
      pc.onnegotiationneeded = makeOffer

      pc.addEventListener("connectionstatechange",()=>{
        console.log("WebRTC: ",pc.connectionState)
      })
      pc.addEventListener("track",(e)=>{
        console.log("received track event")
        const video_element = document.querySelector("#video")
        video_element.srcObject = e.streams[0]
        try {
          //video_element.play()
        } catch (error) {
          
        }
      })
    }

  }, [pc]);

  return (
    <div className="App">
      <header className="App-header">
        <video id="video" controls autoPlay></video>
    <button onClick={()=>sendJsonMessage({event:'connect',room:"room1"})}>Connect to bot</button>
      </header>
    </div>
  );
}

export default App;
