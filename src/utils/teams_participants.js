(()=>{
  function togglePin(subjectName) {

    const attendeesParent = document.querySelector("[aria-label='Participants']")

    const attendeesContainers = attendeesParent.querySelectorAll("li[role='presentation'][data-cid='roster-participant']")

    //unpin all pinned
    document.querySelectorAll('button[data-track-action-outcome="unpinParticipant"]').forEach((element)=>{
      console.log("unpinned")
      element.click()
    })

    attendeesContainers.forEach(async element => {
      const name = element.querySelector('span[id*="roster-avatar-img"]').textContent
      const pinned = element.querySelector('svg[data-cid="roster-participant-pinned"]')
      element.click()   


      if (name == subjectName) {

        if (!pinned) {
          console.log(name,"not pinned. should pin")
          setTimeout(()=>{
            window.waitForElement(".//button[@data-cid='ts-participant-action-button']",element,(e)=>e.click());
            window.waitForElement("//span[text()='Pin for me']",document,(e)=>e.click())
          },1000)

        }
      }
    });
  }

  const wsManager = new window.WebsocketConnection("",{websocket:window.socket,roomJoined:true})
  wsManager.connect(({data}) => {
      const jsonData = JSON.parse(data)
      if (jsonData?.event == "subject") {
        togglePin(jsonData.data)   
      }
  })
  const attendeesDiv = document.querySelector('div[aria-label="Attendees"]');
  let processNodesTimer;
  function processNodes() {
    // Find all spans with 'roster-avatar-img' in their id
    const attendeesParent = document.querySelector("[aria-label='Participants']")

    const attendeesContainers = attendeesParent.querySelectorAll("li[role='presentation'][data-cid='roster-participant']")
    const participantsList = [];

    attendeesContainers.forEach(element => {
      const name = element.querySelector('span[id*="roster-avatar-img"]').textContent

      participantsList.push(name);
    });

    // Send collected text contents to backend

    wsManager.sendParticipants(participantsList)
    console.log(participantsList)
  }

  let quitTimeout;

  function setParticipantsTimeout() {
    const attendeesParent = document.querySelector("[aria-label='Participants']")

    const numberOfAttendees = attendeesParent.querySelectorAll("li[role='presentation'][data-cid='roster-participant']").length
    if (numberOfAttendees < 3) {
      quitTimeout = setTimeout(()=>{
        throw QuitError()
      },TIME_TO_QUIT)  

    }
    else{
      clearTimeout(quitTimeout)
    }
  }

  if (attendeesDiv) {

    setParticipantsTimeout() // quitting if total participants < 3

    // Create a mutation observer to watch for changes
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType == node.ELEMENT_NODE && !node.hasAttribute('data-cid') && node.getAttribute('data-cid') != "roster-participant-pinned") {

            if (processNodesTimer != null && processNodesTimer != undefined) {
              clearTimeout(processNodesTimer)
            }
            processNodesTimer = setTimeout(() => {

              processNodes();
            }, 500); 

          setParticipantsTimeout()
          }
        });

        mutation.removedNodes.forEach(node => {
          if (node.nodeType == node.ELEMENT_NODE && !node.hasAttribute('data-cid') && node.getAttribute('data-cid') != "roster-participant-pinned") {

            if (processNodesTimer != null && processNodesTimer != undefined) {
              clearTimeout(processNodesTimer)
            }
            processNodesTimer = setTimeout(() => {

              processNodes();
            }, 500); 

          setParticipantsTimeout()
          }
        });
      });
    });

    // Configure the observer to watch for child list changes
    observer.observe(attendeesDiv, { childList: true, subtree: true });

  }
})();
