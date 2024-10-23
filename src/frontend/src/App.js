import React, { useEffect, useRef, useState } from "react";
import { ReadyState } from "react-use-websocket";
import { useWebSocket } from "react-use-websocket/dist/lib/use-websocket";
import io from "socket.io-client";

const ICETRANSPORTPOLICY = 'all'
const App = () => {
  const [pc, setPc] = useState(
    new RTCPeerConnection({iceServers: [
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
    ],iceTransportPolicy:ICETRANSPORTPOLICY})
  );
  const [polite, setPolite] = useState(true);
  const [makingoffer, setMakingOffer] = useState(false);
  const [ignoreoffer, setIgnoreOffer] = useState(false);
  const [issettingremoteanswerpending, setIsssettingremoteanswerpending] =
    useState(false);
  const [userId, setUserId] = useState(Date.now());
  const [inputValue, setInputValue] = useState("");

  pc.onicecandidate = (event) => {
    console.log("onicecandidate", event);
    if (event.candidate) {
      socket.current.emit(
        "candidate",
        JSON.stringify({
          from: userId,
          to: "bot",
          candidate: event.candidate,
        })
      );
    }
  };

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };

  const socket = useRef(null);

  const handleMessage = async (message) =>{
      let msg;
      try {
        msg = JSON.parse(message);
      } catch (error) {
        msg = message;
      }
      console.log("msg: ",msg)
      const { event, description, candidate, from, to } = msg;
      if (from != "bot" || to != userId) return  // reject eveything that's not from the bot
      try {
        if (description) {
          // an offer may come in while we are busy processing srd(answer).
          // in this case, we will be in "stable" by the ime the offer is processed
          // so it is safe to chain it on our operations chain now.
          console.log(
            makingoffer,
            pc.signalingstate,
            issettingremoteanswerpending
          );
          const readyforoffer =
            !makingoffer &&
            (pc.signalingstate == "stable" || issettingremoteanswerpending);
          console.log(readyforoffer);
          console.log(description.type, readyforoffer);
          const offercollision = description.type == "offer" && !readyforoffer;

          console.log(offercollision);
          setIgnoreOffer(!polite && offercollision);
          if (ignoreoffer) {
            return;
          }
          setIsssettingremoteanswerpending(description.type == "answer");
          await pc.setRemoteDescription(description); // srd rolls back as needed
          setIsssettingremoteanswerpending(false);
          if (description.type == "offer") {
            console.log("Inside offer");
            await pc.setLocalDescription();
            socket.current.emit(
              pc.localDescription.type,
              JSON.stringify({
                to: "bot",
                from: userId,
                description: pc.localDescription,
              })
            );
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
      } //};
  }

  useEffect(() => {
    //socket.current = io("http://5.161.229.199:7000");
    socket.current = io("http://localhost:7000");
    socket.current.on("connect", () => {
      socket.current.emit("join-room-for-new-bot", "b1786fdc-1120-41a5-8f7c-3deebdcdd71f");
      console.log("connected");
    });
    socket.current.on("disconnect", () => {
      console.log("disconnected");
    });
    socket.current.on("answer", handleMessage)
    socket.current.on("candidate", handleMessage)
    socket.current.on("offer", handleMessage)
    socket.current.on("test", ()=>{
      console.log("got test message")
    })
    socket.current.on("error", (error) => {
      console.log("error", error);
    });
  }, []);

  const handleClick = () => {
    // Call the function with the input value
    socket.current.emit("select-subject", {
      data: inputValue,
    });
  };

  const makeOffer = async () => {
    setPc(
      new RTCPeerConnection({iceServers: [
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
    ],iceTransportPolicy:ICETRANSPORTPOLICY})
    );
    try {
      setMakingOffer(true);
      await pc.setLocalDescription();
      console.log("making offer");
      socket.current.emit(
        pc.localDescription.type,
        JSON.stringify({
          from: userId,
          to: "bot",
          description: pc.localDescription,
        })
      );
      console.log(
        {
          event: pc.localDescription.type,
          from: userId,
          to: "bot",
          description: pc.localDescription,
        },
        "sent"
      );
    } catch (err) {
      console.error(err);
    } finally {
      setMakingOffer(false);
    }
  };

  useEffect(() => {
    if (pc) {
      console.log("Inside PC");
      // let the "negotiationneeded" event trigger offer generation
      pc.onnegotiationneeded = makeOffer;

      pc.addEventListener("connectionstatechange", () => {
        console.log("WebRTC: ", pc.connectionState);
      });
      pc.addEventListener("track", (e) => {
        console.log("received track event");
        const video_element = document.querySelector("#video");
        if (e.streams && e.streams[0]) {
          video_element.srcObject = e.streams[0];
        } else {
          let inboundStream = new MediaStream(e.track);
          video_element.srcObject = inboundStream;
        }
        video_element.play().catch(error => console.error("Error playing video:", error));
      });

      pc.onerror = (event) => {
        console.error("PeerConnection error:", event);
      };

      pc.onconnectionstatechange = (event) => {
        console.log("Connection state change:", pc.connectionState);
        if (pc.connectionState === 'failed') {
          console.error("Connection failed");
        }
      };
    }
  }, [pc]);

  const connectToBot = () => {
    socket.current.emit(
      "livestream", 
      JSON.stringify({ to: "bot", from: userId })
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <video id="video" controls autoPlay></video>
        <button onClick={() => connectToBot()}>Connect to bot</button>
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
};

export default App;
