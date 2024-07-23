(()=>{
  // Function to handle mutations
  function handleMutations(mutationsList) {
    const participantNames = []; // List to collect text from spans

    for (const mutation of mutationsList) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE && node.getAttribute('role') === 'listitem' && node.hasAttribute('participant-id')) {
            console.log('Added:', node);

            // Extract text from span with class="zWGUib" inside the added node
            const spans = node.querySelectorAll('span.zWGUib');
            spans.forEach(span => {
              participantNames.push(span.textContent.trim());
            });
          }
        });

        mutation.removedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE && node.getAttribute('role') === 'listitem' && node.hasAttribute('participant-id')) {
            console.log('Removed:', node);

            // Optionally handle removal of spans or other specific logic
          }
        });

        // Send collected span texts to backend
        if (participantNames.length > 0) {
          console.log(participantNames)
          //sendToBackend(participantNames);
          participantNames.length = 0; // Clear the list after sending
        }
      }
    }
  }
  function toggleParticipants() {
    const button = document.querySelector('button[aria-label="Show everyone"]');

    if (!button) {
      console.error('Button not found.');
      return;
    }

    // Click the button and check aria-pressed attribute
    function verifyAriaPressed(expected) {
      const value = button.getAttribute('aria-pressed');
      console.assert(value === expected || (expected === 'undefined' && value === null), 
        `Expected aria-pressed="${expected}", got="${value}"`);
    }

    button.click();
    verifyAriaPressed('true');

    button.click();
    verifyAriaPressed('undefined');
  }
  // Select the target node

  toggleParticipants()
  const targetNode = document.querySelector('div[aria-label="Participants"]');

  if (targetNode) {
    // Create an observer instance linked to the callback function
    const observer = new MutationObserver(handleMutations);

    // Options for the observer (which mutations to observe)
    const config = { childList: true, subtree: true };

    // Start observing the target node for configured mutations
    observer.observe(targetNode, config);
  } else {
    console.error('Target node with aria-label="Participants" not found.');
  }
  toggleParticipants()

})()
