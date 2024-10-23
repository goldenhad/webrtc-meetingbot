import React, { useEffect, useRef, useState } from 'react';
import { ReadyState } from 'react-use-websocket';
import { useWebSocket } from 'react-use-websocket/dist/lib/use-websocket';

const App = () => {
  const [pc,setPc] = useState(null)
  const [polite,setPolite] = useState(true)
  const [makingoffer,setMakingOffer] = useState(false)
  const [ignoreoffer,setIgnoreOffer] = useState(false)
  const [issettingremoteanswerpending,setIsssettingremoteanswerpending] = useState(false)
  const [userId, setUserId] = useState(Date.now())
  const [inputValue, setInputValue] = useState('');

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };


  const { readyState,sendJsonMessage} = useWebSocket("ws://5.161.229.199:7000/",
    {
      onMessage:
      async ({data}) => {
        const message = JSON.parse(data);
        const {event, description, candidate, from, to} = message;

        if (from != "bot" || to != userId) return  // reject eveything that's not from the bot
        if (pc) {
          console.log("")
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
                sendJsonMessage({ event: pc.localDescription.type,to:"bot", room: 'room1',from:userId, description: pc.localDescription })
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
        }
      },
      shouldReconnect: () => true,

    }
  )
  const handleClick = () => {
    // Call the function with the input value
    sendJsonMessage({event:"select-subject",data:inputValue});
  };

  useEffect(()=>{
    if (readyState == ReadyState.OPEN) {
      sendJsonMessage({ event: 'join-room', room: 'room1' }) 
    }
    console.log('readystate',readyState)
  },[readyState])

  const makeOffer = async () =>{
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
    try {
      setMakingOffer(true)
      await pc.setLocalDescription();
      console.log("making offer")
      sendJsonMessage({ event: pc.localDescription.type, room: 'room1',from:userId,to:"bot", description: pc.localDescription })
    } catch (err) {
      console.error(err);
    } finally {
      setMakingOffer(false)
    }

  }

  useEffect(() => {


    if (pc) {

      // send any ice candidates to the other peer
      pc.onicecandidate = ({candidate}) => sendJsonMessage({ event: 'candidate',to:"bot", room: 'room1',from:userId, candidate: candidate })  
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

  const connectToBot = () =>{
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
    ]}));
    sendJsonMessage({event:"livestream",to:"bot",from:userId,room:'room1'});
  }


  return (
    <div className="App">
    <header className="App-header">
    <video id="video" controls autoPlay></video>
    <button onClick={()=>connectToBot()}>Connect to bot</button>
    <input 
    type="text" 
    value={inputValue} 
    onChange={handleInputChange} 
    placeholder="Enter subject name" 
    />
    <button onClick={handleClick}>Submit</button>
    </header>
    </div>
  );
}

export default App;
