(()=>{

  const wsManager = new window.WebsocketConnection("",{websocket:window.socket,roomJoined:true})

  const label = document.querySelector("button[aria-label='Turn off captions']")
  if (label != null) {

    // Select the target node
    const targetNode = Array.from(document.querySelectorAll('div[class="iOzk7"]')).find((item) => 
      window.getComputedStyle(item).display != "none"
    ); // captions holder

    // Create an observer instance linked to the callback function
    const observer = new MutationObserver((mutationsList, observer) => {
      for(let mutation of mutationsList) {
        if (mutation.type === 'childList' || mutation.type === 'subtree') {
          // Get direct div children of the target node
          const transcriptSections = targetNode.querySelectorAll(':scope > div');
          transcriptSections.forEach(section=>{
            let content = ""
            let author = ""
            const spans = section.querySelectorAll('span');
            author = section.querySelector("div > div:first-child > div").textContent
            spans.forEach((span)=>{
              content += span.textContent + ' ';
            })

            wsManager.sendTranscription(
              author,
              content.trim(),
              Date.now(),
              Date.now()
            )  
          })
        }
      }
    });
    // Options for the observer (which mutations to observe)
    const config = { childList: true, subtree: true };

    // Start observing the target node for configured mutations
    observer.observe(targetNode, config);

  }

})();
