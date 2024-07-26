(()=>{
  try {
    function delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }

    async function togglePin(participantName) {
      participantElements = document.evaluate('//div[@aria-label="Participants"]//div[@role="listitem" and @data-participant-id]',
        document,
        null,
        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
        null
      )
      for (let i = 0; i < participantElements.snapshotLength; i++) {
        let participant = participantElements.snapshotItem(i);
        let pinIcon = document.evaluate(
          './/i[text()="keep"]',
          participant,
          null,
          XPathResult.FIRST_ORDERED_NODE_TYPE,
          null
        ).singleNodeValue;
        scrollTo(participant)

        if (pinIcon) {
          // pinned icon found in participant. If pinned person is not subject, unpin
          if (participant.querySelector('span.zWGUib')?.textContent != participantName) {
            participant.querySelector("button[aria-label='More actions']").click()
            await delay(1000)
            const unpin = await window.waitForElementAsync("//span[text()='Unpin']",document)
            unpin.click()
          }
        } else {
          if (participant.querySelector('span.zWGUib')?.textContent == participantName) {
            participant.querySelector("button[aria-label='More actions']").click()
            const pin = await window.waitForElementAsync("//span[text()='Pin to screen']",document)
            pin.click()
            await delay(1000)
            const myself = await window.waitForElementAsync("//*[text()='For myself only']",document)
            myself.click()
          }
        }
        await delay(1000)
        console.log("ran")
      }
    }

    const wsManager = new window.WebsocketConnection("",{websocket:window.socket,roomJoined:true})
    wsManager.connect(({data}) => {
      console.log("got message")
      const jsonData = JSON.parse(data)

      if (jsonData?.event == "select-subject") {
        togglePin(jsonData.data)   
      }
    })

    let quitTimeout;

    function handleMutations(mutationsList) {
      const participantNames = []; // List to collect text from spans

      for (const mutation of mutationsList) {
        if (mutation.type === 'childList') {

          const participantNumber = document.evaluate(
            "count(//*[@role='listitem and @data-participant-id])",
            document,
            null,
            XPathResult.NUMBER_TYPE
          ).numberValue

          if (participantNumber < 3) {
            console.log("Only 1 other user... Starting timer")
            quitTimeout = setTimeout(()=>{
              throw QuitError()
            },TIME_TO_QUIT)  
          }
          else{
            console.log("User joined... Removing timer")
            clearTimeout(quitTimeout)
          }

          mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE && node.getAttribute('role') === 'listitem' && node.hasAttribute('data-participant-id')) {
              console.log('Added:', node);


              // Extract text from span with class="zWGUib" inside the added node
              const spans = document.querySelectorAll('div[aria-label="Participants"] span.zWGUib');
              spans.forEach(span => {
                participantNames.push(span.textContent.trim());
              });
            }
          });

          mutation.removedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE && node.getAttribute('role') === 'listitem' && node.hasAttribute('data-participant-id')) {
              console.log('Removed:', node);

              const spans = document.querySelectorAll('div[aria-label="Participants"] span.zWGUib');
              spans.forEach(span => {
                participantNames.push(span.textContent.trim());
              });
              // Optionally handle removal of spans or other specific logic
            }
          });

          // Send collected span texts to backend
          if (participantNames.length > 0) {
            console.log(participantNames)
            wsManager.sendParticipants(participantNames)        
            participantNames = []; // Clear the list after sending
          }
        }
      }
    }
    const targetNode = document.querySelector('div[aria-label="Participants"]');

    if (targetNode) {
      console.log("got targetnode")
      // Create an observer instance linked to the callback function
      const observer = new MutationObserver(handleMutations);
      const participantCountObserver = new MutationObserver(handleMutations);


      // Options for the observer (which mutations to observe)
      const config = { childList: true, subtree: true };

      // Start observing the target node for configured mutations
      observer.observe(targetNode, config);
    } else {
      console.error('Target node with aria-label="Participants" not found.');
    }

  } catch (error) {
    console.error(error) 
    if (error instanceof QuitError) {
      throw error 
    }
  }

})();
