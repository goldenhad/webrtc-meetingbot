(()=>{
  try {

    //get all participant elements
    //iterate through them
    //see whether theres pin icon in any of htem
    //if there is, unpin
    //then pin the new guy
    async function togglePin(participantName) {
      participantElements = document.evaluate('//div[@aria-label="Participants"]//div[@role="listitem" and @data-participant-id]',
        document,
        null,
        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
        null
      )
      for (let i = 0; i < participantElements.snapshotLength; i++) {
        let participant = participantElements.snapshotItem(i);
        let keepElement = document.evaluate(
          './/i[text()="keep"]',
          participant,
          null,
          XPathResult.FIRST_ORDERED_NODE_TYPE,
          null
        ).singleNodeValue;
        scrollTo(participant)

        if (keepElement) {
          // pinned icon found in participant
          console.log("Found 'pinnned' in participant:", participant);
          if (keepElement.querySelector('span.zWGUib')?.textContent != participantName) {
            keepElement.querySelector("button[aria-label='More actions]").click()
            const unpin = await window.waitForElement("//*[text()='Unpin']") 
            unpin.click()
          } 
        } else {
          participant.querySelector("button[aria-label='More actions]").click()
          const pintoScreen = await window.waitForElement("//span[text()='Pin to the screen']")
          pintoScreen.click()
          const forMyself = await window.waitForElement("//[text()='For myself only']")
          forMyself.click()
          console.log("No 'pinned' found in participant:", participant);
        }
      }

    }

    const wsManager = new window.WebsocketConnection("",{websocket:window.socket,roomJoined:true})
    wsManager.connect((message) => {
      const jsonData = JSON.parse(message)
      if (jsonData?.event == "subject") {
        togglePin(jsonData.data)   
      }
    })

    function handleMutations(mutationsList) {
      const participantNames = []; // List to collect text from spans

      for (const mutation of mutationsList) {
        if (mutation.type === 'childList') {
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


      // Options for the observer (which mutations to observe)
      const config = { childList: true, subtree: true };

      // Start observing the target node for configured mutations
      observer.observe(targetNode, config);
    } else {
      console.error('Target node with aria-label="Participants" not found.');
    }

  } catch (error) {
    console.error(error) 
  }

})();
