define(['WebSDK', 'ojs/ojcore'], function (WebSDK, oj) {
  'use strict'; // require(['ojs/ojcore'], function(oj) {

  let eventHelper;
  let socket; // For Auto-Suggestions
  let currentTypedText;  // For Auto-Suggestions

  let hasStartedConversation = false;

  let hasStartedNEWConversation = false; // Added on 16 June - for handling NEW CONVERSATIONS button click within the ODA
  let hasReceievedNEWConversation = false;
  let hasReceievedPayables = false;

  const PageModule = function PageModule(context) {


    eventHelper = context.getEventHelper();
  };

  function getUri() {
    return "oda-xxx.data.digitalassistant.oci.oraclecloud.com";
  }

  function getChannelId() {
    return "channel-id"; 
  }

  let isClientAuthEnabled = false;


  // Initialize bot
  PageModule.prototype.init = function (fullname, application) {
    console.log("Initializing bot..." + fullname);
    sessionStorage.setItem("openRightPanelInsights", false);  // reset this
    sessionStorage.setItem("openLeftPanelInsights", true);   // LEFT panel is opened on the application load

    const chatSettings = {
      URI: getUri(),
      clientAuthEnabled: isClientAuthEnabled,     // Enables client auth enabled mode of connection if set true, no need to pass if set false
      channelId: getChannelId(),
      /* START CUSTOMIZATION FOR DEMO*/
      //delegate: _delegateObject,
      disablePastActions: 'none',
      enableDraggableButton: true,
      initUserProfile: { profile: { firstName: application.user.username, lastName: 'Doe', email: 'john.doe@example.com', timezoneOffset: (new Date()).getTimezoneOffset() * 60 * 1000, properties: { browserLanguage: navigator.language, uiUserToken: application.variables.idcsToken, uiUserId: application.user.username } } },
      height: '1100px',
      width: '900px',
      //height: '100vh', //layout modification property
      //width: '50vw',  //layout modification property
      //linkHandler: { target: 'background_frame' },
      webViewConfig: { referrerPolicy: 'no-referrer-when-downgrade', closeButtonType: 'label', closeButtonLabel: 'Close', size: 'full', title: 'Ask Oracle' },
      /* END CUSTOMIZATION FOR DEMO*/
      enableAutocomplete: false,                   // Enables autocomplete suggestions on user input
      enableBotAudioResponse: true,               // Enables audio utterance of skill responses
      enableClearMessage: true,                   // Enables display of button to clear conversation
      enableSpeech: false,                         // Enables voice recognition
      speechLocale: WebSDK.SPEECH_LOCALE.EN_US,   // Sets locale used to speak to the skill, the SDK supports EN_US, FR_FR, and ES_ES locales for speech
      showConnectionStatus: true,                 // Displays current connection status on the header
      i18n: {                                     // Provide translations for the strings used in the widget
        en: {                                   // en locale, can be configured for any locale
          chatTitle: 'Ask Oracle'    // Set title at chat header
        },
        de: {
          chatTitle: "Web SDK Anwendungsbeispiele"
        }
      },
      timestampMode: 'relative',                  // Sets the timestamp mode, relative to current time or default (absolute)
      theme: WebSDK.THEME.CLASSIC,            // Redwood dark theme THEME.REDWOOD_DARK. The default is THEME.DEFAULT, while older theme is available as THEME.CLASSIC
      messagePadding: '4px 4px',
      //userId: '<userID>',                         // User ID, optional field to personalize user experience
      ttsVoice: [{ lang: 'en-us' }],
      openChatOnLoad: false,
      enableAttachment: false,                 // Sets the timestamp mode, relative to current time or default (absolute)
      icons: {
        logo: application.path + 'resources/images/iconProfile.png',
        avatarAgent: application.path + 'resources/images/bot-image.png',
        avatarUser: application.path + 'resources/images/bot-image.png',
        avatarBot: application.path + 'resources/images/iconProfile.png',
        //typingIndicator: 'resources/images/typing.gif'
      },
      initUserHiddenMessage: 'Greetings'
      //,alwaysShowSendButton: true
      , actionsLayout: 'horizontal'
      , cardActionsLayout: 'horizontal'
      , formActionsLayout: 'horizontal'
      , globalActionsLayout: 'horizontal'
      , customHeaderElementId: 'customMenu'
      //,openLinksInNewWindow: true
      , linkHandler: { target: 'oda-chat-webview' }
      //,enableResizableWidget: true
      //,customHeaderElementId: 'customMenu'
      //,enableEndConversation: false
      //displayActionAsPills: true,
      //showTypingIndicator: true,
      //enableDefaultClientResponse: true,
      //enableSendTypingStatus: true
    };


    //





    // Setup input listener after SDK is initialized
    setupInputListener();
    setupSendButtonListener();
    setupWebSocket();


    // document.getElementById('trustedIcon').onclick = function(event) { // collapsible-panel

    //    document.getElementById('collapsible-panel').style = "display: block";

    // };




    setTimeout(() => {
      window.Bots = new WebSDK(chatSettings);

      window.Bots.connect().then(() => {

        console.log("Connection Successful");
        window.Bots.on('message:sent', function (message) {
          console.log('the user sent a messageee-INIT:', message.messagePayload.text);
          if (message.messagePayload.text === 'New Conversation') {
            console.log('NEW CONVERSATION RECEIVED');
            hasStartedNEWConversation = true; // hasStartedNEWConversation
          }
          if (message.messagePayload.text === 'Payables') { // Payables
            console.log('Payables RECEIVED');
            hasReceievedPayables = true; // hasReceievedPayables
          }
          if (message.messagePayload.text === 'Explore Dataset') {
            console.log('Explore Dataset RECEIVED');
            //hasStartedNEWConversation = true; // hasStartedNEWConversation
          }

        });

      }, (reason) => {
        console.log("Connection failed");
        console.log(reason);
      });
    }, 0);
  };

  // For Auto-Suggestions in the 

  function setupSendButtonListener() {
    console.log(" IN setupSendButtonListener");
    const sendButton = document.evaluate(
      '/html/body/div[2]/div/div[3]/div/div/button',
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null
    ).singleNodeValue;




    if (sendButton) {
      sendButton.addEventListener('click', hideSuggestionContainer);
    } else {
      console.error('Send button not found');
      setTimeout(setupSendButtonListener, 1000);
    }
  }



  let latestUserInput = "";  // tracker for fetching the last but one value otherwise it is going as null for ENTER so -- // Modified on 16th June

  function handleInput(event) {
    //const inputValue = event.target.value;
    latestUserInput = event.target.value.trim();
    console.log("INNN handleInput - Value:", latestUserInput);
  }

  let typedMessage = '';


  function handleKeyup(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      console.log("ENTER Pressed - value:", latestUserInput);

      if (latestUserInput) {
        sendInputToServer(latestUserInput);

        if (hasStartedNEWConversation) { // call only on NEW CONVERSATION clicks
          setTimeout(() => {
            console.log("It's a NEW CONVERSATION: ", latestUserInput);
            hasStartedNEWConversation = false;
            eventHelper.fireCustomEvent("fetchConversationsEvent", {
              payload: latestUserInput
            });
          }, 3000);

        }
        else {
          console.log("NOT a NEW CONVERSATION");
        }



      } else {
        console.warn("ENTER Pressed but input is invalid.");
      }
    }
  }

  function setupInputListener() {
    console.log("INNN  Calling setupInputListener");

    setCollapsible();

    const observer = new MutationObserver(() => {
      const textarea = document.getElementById('oda-chat-user-text-input');

      if (textarea) {
        console.log("INNN  Textarea found");


        // textarea.removeEventListener('input', handleInput);
        // textarea.removeEventListener('keyup', handleKeyup);

        textarea.addEventListener('input', handleInput);
        textarea.addEventListener('keyup', handleKeyup);



        observer.disconnect(); // Disconnect once attached
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    console.log("setupInputListener done");
  }


  function setupInputListener3() {
    console.log("Calling setupInputListener initial");
    setCollapsible();

    const observer = new MutationObserver((mutations) => {

      const textarea = document.getElementById('oda-chat-user-text-input');
      console.log("setupInputListener textarea1: " + textarea.value);


      if (textarea) {
        // document.addEventListener("keyup", function (event) {
        //   if (event.key === "Enter" && !event.shiftKey) {
        //     event.preventDefault();
        //     const textarea2 = document.querySelector("oda-chat-user-text-input");
        //     console.log("ENTER Presseddd. textarea2:", textarea2.value);

        //     const inputText = textarea2?.value?.trim();

        //     console.log("ENTER Presseddd. Input Text:", inputText);

        //     if (inputText) {
        //       sendInputToServer(inputText);

        //       setTimeout(() => {
        //         eventHelper.fireCustomEvent("fetchConversationsEvent", {
        //           payload: inputText
        //         });
        //       }, 1000);
        //     }
        //   }
        // });

        console.log("Creating the INPUT EVENT. - handleInput ");
        textarea.addEventListener('input', handleInput);
        observer.disconnect();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    console.log("Calling setupInputListener done");
  }




  function setupInputListener2() {

    console.log("Calling setupInputListener");
    setCollapsible();

    // const textarea1 = document.getElementById('oda-chat-user-text-input');
    // textarea1.addEventListener('keydown', function (event) {
    //   if (event.key === 'Enter' && !event.shiftKey) {
    //     event.preventDefault(); // prevent newline on Enter
    //     console.log("textarea1.value: "+textarea1.value);
    //     sendInputToServer(textarea1.value);
    //   }
    // });


    console.log("Calling setupInputListener done");

    const observer = new MutationObserver((mutations) => {
      const textarea = document.getElementById('oda-chat-user-text-input');
      console.log("textarea1: " + JSON.stringify(textarea));
      if (textarea) {

        textarea.addEventListener('keyup', function (event) {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // prevent newline on Enter
            console.log("textarea: " + textarea.value);
            sendInputToServer(textarea.value);
          }
        });

        textarea.addEventListener('input', handleInput);
        observer.disconnect();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  function handleInput2(event1) {
    console.log("IN handleInput");
    // setCollapsible();

    console.log("In handleInput start: " + event1.target.value);

    const observer = new MutationObserver((mutations) => {

      const textarea = document.getElementById('oda-chat-user-text-input');
      console.log("handleInput textarea1: " + textarea.value);


      if (textarea) {
        document.addEventListener("keyup", function (event) {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            const textarea2 = document.querySelector("oda-chat-user-text-input");
            console.log("ENTER Presseddd. textarea2:", textarea2.value);

            const inputText = textarea2?.value?.trim();

            console.log("ENTER Presseddd. Input Text:", inputText);
            if (inputText) {
              sendInputToServer(inputText);

              setTimeout(() => {
                eventHelper.fireCustomEvent("fetchConversationsEvent", {
                  payload: inputText
                });
              }, 1000);
            }
          }
        });

        console.log("Creating the INPUT EVENT. - handleInput ");
        textarea.addEventListener('input', handleInput);
        observer.disconnect();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }






  /*
      const words = event.target.value.trim().split(/\s+/);
      if (words.length >= 3) {
        sendInputToServer(event.target.value);
        console.log("fetchConversationsEvent-handleInput-words>3 => event.target.value : " + event.target.value);
   
   
        let anchor = document.getElementsByTagName("a");
        let href = anchor[1].href;
        console.log("href::: " + href);
   
   
      } else {
        hideSuggestionContainer();
      }
   
      */




  function sendInputToServer(input) {
    console.log(" INNNN sendInputToServer input: " + JSON.stringify(input)); // ONLY PLACE FOR NOW - 25TH MAY 2025





    if (socket && socket.readyState === WebSocket.OPEN) {
      console.log(JSON.stringify({ InputToSocketAPI: input }));
      socket.send(JSON.stringify({ message: input }));
      currentTypedText = input;
    }
    console.log("fetchConversationsEvent-sendInputToServer =>");
    //eventHelper.fireCustomEvent("fetchConversationsEvent", { payload: input }); // ONLY PLACE FOR NOW - 25TH MAY 2025
  }


  let retryCount = 0;
  const maxRetries = 5;

  function setupWebSocket() {

    if (retryCount >= maxRetries) {
      console.warn("Max WebSocket retry limit reached. Stopping re-attempts.");
      return;
    }

    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      console.log("WebSocket is already open or connecting");
      return;
    }

    socket = new WebSocket('wss://207.211.161.208.sslip.io:8003/ws/suggestions');



    socket.onopen = function () {
      console.log('WebSocket connection established');
      retryCount = 0; // Reset
    };

    socket.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        if (data && Array.isArray(data.message) && data.message.length > 0) {
          displaySuggestions(data.message, currentTypedText);
        } else {
          console.log('No suggestions to display');
        }
      } catch (error) {
        console.error('Error parsing suggestions:', error);
      }
    };

    socket.onerror = function (error) {
      console.error('WebSocket error:', error);
    };

    socket.onclose = function (event) {

      if (retryCount < maxRetries) {
        retryCount++;
        setTimeout(() => {
          setupWebSocket();
        }, 5000);
      }
    };
  }

  function displaySuggestions(suggestions, typedText) {
    var suggestionContainer = document.getElementById('oda-chat-suggestions-list');
    suggestionContainer.innerHTML = '';

    const inputField = document.evaluate(
      '//*[@id="oda-chat-user-text-input"]',
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null
    ).singleNodeValue;

    const inputRect = inputField.getBoundingClientRect();

    // Updated container styling with minimal margins
    Object.assign(suggestionContainer.style, {
      position: 'absolute',
      zIndex: '100001',
      backgroundColor: '#f5f5f5',
      border: '1px solid #ccc',
      borderRadius: '4px',
      boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
      maxHeight: '150px',
      overflowY: 'auto',
      width: '100%', // Changed from calc(100% - 20px)
      display: suggestions.length > 0 ? 'block' : 'none',
      // bottom: `${window.innerHeight - inputRect.top - 52}px`,
      left: '0', // Removed left padding
      right: '0', // Removed right padding
      margin: '0', // Explicitly set margin to 0
      padding: '0' // Explicitly set padding to 0
    });

    suggestions.forEach(function (suggestion) {
      const button = document.createElement('button');
      var highlightedSuggestion = suggestion.text;

      if (suggestion.entities) {
        suggestion.entities.forEach(([entityText, entityType]) => {
          const entityRegex = new RegExp(entityText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
          highlightedSuggestion = highlightedSuggestion.replace(entityRegex,
            `<mark class="entity" data-entity="${entityType}">$&</mark>`);
        });
      }

      const typedTextRegex = new RegExp(`(${typedText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      highlightedSuggestion = highlightedSuggestion.replace(typedTextRegex,
        '<span style="font-weight: bold;">$1</span>');

      button.innerHTML = highlightedSuggestion;

      button.onclick = function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (inputField) {
          inputField.value = suggestion.text;
          inputField.focus();
        }
        suggestionContainer.innerHTML = '';
        suggestionContainer.style.display = 'none';
      };

      // Updated button styling with minimal left spacing
      Object.assign(button.style, {
        display: 'block',
        width: '100%',
        textAlign: 'left',
        padding: '8px 4px', // Reduced left/right padding
        border: 'none',
        backgroundColor: 'transparent',
        cursor: 'pointer',
        margin: '0',
        fontSize: '12px',
        lineHeight: '1.4',
        fontFamily: 'inherit',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        boxSizing: 'border-box', // Ensure padding is included in width calculation
        paddingLeft: '4px' // Explicitly set left padding to minimum
      });

      button.onmouseover = () => button.style.backgroundColor = '#f0f0f0';
      button.onmouseout = () => button.style.backgroundColor = 'transparent';

      suggestionContainer.appendChild(button);
    });
  }

  function hideSuggestionContainer() {

    //console.log("IN hideSuggestionContainer");


    const textarea = document.getElementById('oda-chat-user-text-input');
    console.log("IN hideSuggestionContainer textarea1: " + textarea.value);

    var suggestionContainer = document.getElementById('oda-chat-suggestions-list');
    if (suggestionContainer) {
      suggestionContainer.style.display = 'none';
      suggestionContainer.innerHTML = '';
    }
    console.log("fetchConversationsEvent-hideSuggestionContainer =>");

    // Modified on 16th June
    // eventHelper.fireCustomEvent("fetchConversationsEvent", { payload: '' });
  }

  PageModule.prototype.closeBot = function () {


    // Close the chat

    window.Bots.closeChat();

  };




  window.chatOpened = false;

  PageModule.prototype.openBotSendMessage = function (messageText) {

    window.Bots.on('message:sent', function (message) {
      console.log('the user sent a messageee', message.messagePayload.text);
      if (message.messagePayload.text === 'New Conversation') {
        console.log('NEW CONVERSATION RECEIVED');
        hasStartedNEWConversation = true; // hasStartedNEWConversation
      }
    });


    window.Bots.on('message:received', function (message) {
      console.log('the user received', message.messagePayload.text);


      if (message.messagePayload.text.trim().includes("I'm starting a new conversation")) {
        hasReceievedNEWConversation = true;
        console.log('Sounds good - YES -  NEW CONVERSATION RECEIVED - ' + hasReceievedNEWConversation);
      } else {
        hasReceievedNEWConversation = false;
        console.log('Sounds good - NO - NEW CONVERSATION NOT RECEIVED - ' + hasReceievedNEWConversation);
      }

    });




    console.log("message text: " + messageText);
    console.log("hasStartedConversation " + hasStartedConversation);

    if (!window.Bots) {
      console.error('Chat bot is not initialized.');
      return;
    }

    window.Bots.openChat();


    if (!hasStartedConversation) {
      window.Bots.connect().then(() => {

        console.log("Chatbot connected for first time.");
        hasStartedConversation = true;



        //window.Bots.sendMessage('Payables', { hidden: true });

        if (!hasReceievedPayables) // only if hasReceievedPayables is false -> to avoid duplicates  added on 15th July 2025 -> issue with duplicate Payables
        {
          console.log("hasReceievedPayables is FALSE so sending the Payables prompt");
          window.Bots.sendMessage('Payables', { hidden: true });

        }



        setTimeout(() => {
          this._sendInput(messageText);
          console.log("fetchConversationsEvent-openBotSendMessage -> IF =>");
          eventHelper.fireCustomEvent("fetchConversationsEvent", { payload: messageText });

          setTimeout(() => { // Modified on 16th June
            eventHelper.fireCustomEvent("fetchConversationsEvent", { payload: messageText });
          }, 2000);


        }, 1000);
      }).catch((err) => {
        console.error('Bot connection failed:', err);
      });
    } else {


      if (!hasReceievedNEWConversation) // only if this is not true, not to send 2 NEW CONVERSATIONS
        window.Bots.sendMessage('New Conversation', { hidden: true });
      // this._sendInput(messageText);
      console.log("fetchConversationsEvent-openBotSendMessage -> ELSE =>");
      this._sendInput(messageText);
      setTimeout(() => { // Modified on 16th June

        eventHelper.fireCustomEvent("fetchConversationsEvent", { payload: messageText });
      }, 1000);
    }
  };

  PageModule.prototype._sendInput = function (messageText) {
    setTimeout(() => {
      const inputField = document.querySelector('#oda-chat-user-text-input');
      const sendButton = document.evaluate(
        '/html/body/div[2]/div/div[3]/div/div/button',
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
      ).singleNodeValue;

      if (inputField && sendButton) {
        inputField.value = messageText;
        const inputEvent = new Event('input', { bubbles: true });
        inputField.dispatchEvent(inputEvent);
        sendButton.click();
        hideSuggestionContainer();
      } else {
        console.error('Input field or send button not found.');
      }
    }, 400);
  };















  function setCollapsible() {
    console.log("showInsights Testing:   1");


    /* * - working
     
     <span class="oda-view-insights" onclick="window.parent.postMessage({ action: 'showInsights' }, '*');">
      View Insights
    </span>
     * 
     * 
     * 
     <span style="cursor:pointer; color:#007bff; text-decoration:underline;" onclick="window.parent.postMessage({ action: 'showInsights' }, '*');">
      View Insights
    </span>
     * 
     */


    // if (!window._showInsightsListenerAdded) {
    //   window.addEventListener('message', function (event) {
    //     if (event.data && event.data.action === 'showInsights') {

    //       console.log("IN showInsights Triggered");
    //       console.log("Received parameter idataId:", event.data.idataId);



    //       sessionStorage.setItem("idataIdSession", event.data.idataId);

    //       console.log("from Sessionn idataIdSession:" + sessionStorage.getItem("idataIdSession"));




    //       let getDetailedInsights = sessionStorage.getItem("getDetailedInsights");
    //       const panel = document.getElementById('right-collapsible-panel');
    //       const odaIframe = document.querySelector('.oda-chat-widget');

    //       console.log("from Sessionn getDetailedInsights:" + getDetailedInsights);
    //       if (panel) {
    //         //console.log("from Sessionn getDetailedInsights:" + sessionStorage.getItem("getDetailedInsights"));
    //         sessionStorage.setItem("getDetailedInsights", true); // for the View Insights link in the chat bot (outside View Full Data Set)
    //         eventHelper.fireCustomEvent("refreshSessionVar_ViewInsights", { payload: getDetailedInsights });
    //         //console.log("from Sessionn getDetailedInsights 11:" + sessionStorage.getItem("getDetailedInsights"));
    //         panel.classList.remove('oj-hidden', 'oj-sm-hide');
    //         panel.style.display = 'block';
    //         panel.setAttribute('expanded', 'true');
    //         //oj.Components.getComponent(panel).option('expanded', true);
    //       }

    //       if (odaIframe) {
    //         console.log("IN showInsights odaIframe");

    //         console.log("ODA widget found:", odaIframe);

    //         //   chatWidget.style.width = '600px';
    //         // chatWidget.style.left = 'calc(49%);';


    //         odaIframe.style.setProperty('width', '52vw', 'important');
    //         odaIframe.style.setProperty('left', '24vw', 'important');



    //         if (odaIframe) {
    //           odaIframe.style.setProperty('--widget-max-width', '76vh', 'important');
    //         }
    //       }
    //     } // end of showInsights


    //     if (event.data && event.data.action === 'getDetailedInsights') { // HIDE the user message and actions panel from RIGHT panel

    //       let getDetailedInsights = sessionStorage.getItem("getDetailedInsights");
    //       const panel = document.getElementById('right-collapsible-panel');
    //       if (panel) {
    //         sessionStorage.setItem("getDetailedInsights", false); // for the View Insights link in the chat bot (outside View Full Data Set)
    //         eventHelper.fireCustomEvent("refreshSessionVar_ViewInsights", { payload: getDetailedInsights });

    //         panel.classList.remove('oj-hidden', 'oj-sm-hide');
    //         panel.style.display = 'block';
    //         panel.setAttribute('expanded', 'true');

    //       }


    //     }

    //     if (event.data && event.data.action === 'autoInsights') { // SHOW the user message and actions panel from RIGHT panel

    //        let getDetailedInsights = sessionStorage.getItem("getDetailedInsights");
    //       const panel = document.getElementById('right-collapsible-panel');
    //       if (panel) {
    //         sessionStorage.setItem("getDetailedInsights", true); // for the View Insights link in the chat bot (outside View Full Data Set)
    //         eventHelper.fireCustomEvent("refreshSessionVar_ViewInsights", { payload: getDetailedInsights });

    //         panel.classList.remove('oj-hidden', 'oj-sm-hide');
    //         panel.style.display = 'block';
    //         panel.setAttribute('expanded', 'true');

    //       }

    //     }

    //     if (event.data && event.data.action === 'hideInsights') {
    //       console.log("IN hideInsights Triggered");

    //       const panel = document.getElementById('right-collapsible-panel');
    //       const odaIframe = document.querySelector('.oda-chat-widget');

    //       if (panel) {
    //         panel.classList.add('oj-hidden');
    //         panel.style.display = 'none';
    //       }

    //       if (odaIframe) {
    //         odaIframe.style.width = '85vh';
    //       }
    //     } // end of hideInsights
    //   });

    //   window._showInsightsListenerAdded = true;
    // }


    if (!window._showInsightsListenerAdded) {
      window.addEventListener('message', function (event) {

        console.log("RECEIVED MESSAGE:", event);
        const action = event?.data?.action;
        const idataId = event?.data?.idataId;
        const calledFrom = event?.data?.calledFrom;
        console.log("Received parameter action:", action);

        const panel = document.getElementById('right-collapsible-panel');
        const odaIframe = document.querySelector('.oda-chat-widget');

        let showLeftPanel = sessionStorage.getItem("openLeftPanelInsights"); // Show left panel
        console.log("LEFT PANEL IN INSIGHTS: " + showLeftPanel);

        switch (action) {
          case 'showInsights': // SHOW user message/actions inside panel
            console.log("INNNNNN showInsights");
            console.log("Received parameter idataId:", idataId);
            console.log("Received parameter calledFrom:", calledFrom);

            sessionStorage.setItem("idataIdSession", idataId);
            sessionStorage.setItem("getDetailedInsights", "true");

            eventHelper.fireCustomEvent("refreshSessionVar_ViewInsights", { payload: "true" });

            if (panel) {
              panel.classList.remove('oj-hidden', 'oj-sm-hide');
              panel.style.display = 'block';
              panel.setAttribute('expanded', 'true');
            }

            if (odaIframe) {
              console.log("IN showInsights odaIframe");
              odaIframe.style.setProperty('width', '52vw', 'important');
              odaIframe.style.setProperty('left', '24vw', 'important');
              odaIframe.style.setProperty('--widget-max-width', '76vh', 'important');

            }
            break;

          case 'getDetailedInsights': // SHOW user message/actions inside panel
            console.log("INNNNNN getDetailedInsights");
            sessionStorage.setItem("getDetailedInsights", "true");
            
            console.log("hererererere:" + sessionStorage.getItem("insightHistorySession"));

            if(sessionStorage.getItem("insightHistorySession") === false){
              console.log("herererererererer");
              eventHelper.fireCustomEvent("clearautoinsights", { payload: "false" });
            }
            //New Code Added -- Shiba
            // if (calledFrom === 'getDetailedInsights') {
            //   showLeftPanel = 'false';
            //   eventHelper.fireCustomEvent("toggleButton", { payload: "false" });
            //   // console.log("showLeft Panel and custom fire even",showLeftPanel);
            // }
            eventHelper.fireCustomEvent("insightsClickleftPanelChainEvent", { payload: "false" }); // Added on 01st July 2025
            eventHelper.fireCustomEvent("refreshSessionVar_ViewInsights", { payload: "true" });
            if (panel) {
              panel.classList.remove('oj-hidden', 'oj-sm-hide');
              panel.style.display = 'block';
              panel.setAttribute('expanded', 'true');

              // if (odaIframe) {
              //   console.log("IN showInsights odaIframe");
              //   odaIframe.style.setProperty('width', '52vw', 'important');
              //   odaIframe.style.setProperty('left', '24vw', 'important');
              //   odaIframe.style.setProperty('--widget-max-width', '76vh', 'important');
              // }

              // resize the chat bot  (odaIframe) based on the left panel - expanded/collapsed
              if (showLeftPanel === 'true' && odaIframe) {
                //If left panel is expanded, and right panel is expanded
                odaIframe.style.setProperty('width', '52vw', 'important');
                odaIframe.style.setProperty('left', '24vw', 'important');
              }
              else {
                //If left panel is collapsed, and right panel is collapsed
                odaIframe.style.setProperty('left', '1vw', 'important');
                odaIframe.style.setProperty('width', '75vw', 'important');
              }

            }
            break;

          case 'autoInsights': // HIDE user message/actions inside panel autoInsights_ServiceCall
            console.log("INNNNNN autoInsights calledFrom: " + calledFrom);
            //console.log("Received parameter calledFrom:", calledFrom);
            sessionStorage.setItem("getDetailedInsights", "false");


            // if (calledFrom === 'autoInsights') {
            //   showLeftPanel = 'false';
            //   eventHelper.fireCustomEvent("toggleButton", { payload: "false" });
            //   console.log("showLeft Panel and custom fire even", showLeftPanel);
            // }
            eventHelper.fireCustomEvent("insightsClickleftPanelChainEvent", { payload: "false" }); // Added on 01st July 2025

            eventHelper.fireCustomEvent("refreshSessionVar_ViewInsights", { payload: "false", calledFrom: calledFrom });
            eventHelper.fireCustomEvent("autoInsights_ServiceCall", { payload: "false" });

            if (panel) {
              panel.classList.remove('oj-hidden', 'oj-sm-hide');
              panel.style.display = 'block';
              panel.setAttribute('expanded', 'true');

              // if (odaIframe) {
              //   odaIframe.style.setProperty('width', '52vw', 'important');
              //   odaIframe.style.setProperty('left', '24vw', 'important');
              //   odaIframe.style.setProperty('--widget-max-width', '76vh', 'important');
              // }


              // resize the chat bot  (odaIframe) based on the left panel - expanded/collapsed
              if (showLeftPanel === 'true' && odaIframe) {
                //If left panel is expanded, and right panel is expanded
                odaIframe.style.setProperty('width', '52vw', 'important');
                odaIframe.style.setProperty('left', '24vw', 'important');
              }
              else {
                //If left panel is collapsed, and right panel is collapsed
                odaIframe.style.setProperty('left', '1vw', 'important');
                odaIframe.style.setProperty('width', '75vw', 'important');
              }

            }
            break;

          case 'hideInsights':
            console.log("IN hideInsights Triggered");

            if (panel) {
              panel.classList.add('oj-hidden');
              panel.style.display = 'none';
            }

            if (odaIframe) {
              odaIframe.style.width = '85vh';
            }
            break;

          case 'newconversation':
            console.log("IN newConversation Triggered");
            hasStartedNEWConversation = true;
            break;
          
           case 'exploreDataset': 
            console.log("INNNNNN exploreDataset calledFrom: ");
            eventHelper.fireCustomEvent("clearautoinsights", { payload: "false" }); 
            break;

          default:
            // Ignore unrecognized actions
            break;




        }
      });

      window._showInsightsListenerAdded = true;
    }











    console.log("showInsights Testing:   2");





    let test = document.getElementById('trustedIcon');
    if (test) {

      test.addEventListener('click', function () {

        let p1 = this.getAttribute("data-name");
        theFunction(p1);
      });
    }

    console.log("Testing:   2");
  }

  function theFunction(data) {

    //alert("JaiMataDi: " + data);

    const chatWidget = document.querySelector('.oda-chat-widget');
    if (chatWidget) {
      console.log("chatWidget is visible");
      chatWidget.style.width = '600px';
      chatWidget.style.left = 'calc(49%);';
      console.log("data: " + data);
      document.getElementById('collapsible-panel').style = "display: block";
    }


  }


  // PageModule.prototype.theFunction = function (data) {
  //   alert("data: " + data);
  // };


  // Hide View Insights Panel on click - RIGHT PANEL
  PageModule.prototype.hideViewInsightsPanel = function (showLeftPanel) {

    console.log("In hideViewInsightsPanel - LEFT PANEL Expanded: " + showLeftPanel);
    sessionStorage.setItem("openRightPanelInsights", false); // this is to handle the chat bot layout on open/close of left panel based on the right panel's visibility




    const panel = document.getElementById('right-collapsible-panel');
    const odaIframe = document.querySelector('.oda-chat-widget');

    if (panel) {
      panel.classList.add('oj-hidden');
      //panel.setAttribute('expanded', 'true');
      panel.style.display = 'none';
    }

    // resize the chat bot  (odaIframe) based on the left panel - expanded/collapsed

    if (odaIframe && showLeftPanel) {
      //If left panel is expanded, and right panel is collapsed
      odaIframe.style.setProperty('width', '76vw', 'important');
      odaIframe.style.setProperty('left', '24vw', 'important');
    }
    else {
      //If left panel is collapsed, and right panel is collapsed
      odaIframe.style.setProperty('left', '5vw', 'important');
      odaIframe.style.setProperty('width', '90vw', 'important');
    }

    console.log("In hideViewInsightsPanel END");

  };

  // Move chat bot on history icon click - close/open - LEFT PANEL
  PageModule.prototype.resizeChatBotOnHistoryIcon = function (showLeftPanel) {

    console.log("11=> resizeChatBotOnHistoryIcon -> Left panel is : " + showLeftPanel);
    //console.log("Right panel is opened/closed: "+sessionStorage.getItem("openRightPanelInsights"));


    // let showRightPanel1 = sessionStorage.getItem("openRightPanelInsights");


    // if (showRightPanel1) {
    //   this.showLeftPanel = false;
    //   console.log("11=> Right panel is  " + showRightPanel1 + " so making LEFT panel: " + this.showLeftPanel);
    // }


    if (showLeftPanel)
      sessionStorage.setItem("openLeftPanelInsights", true); // created this to handle whether left panel is opened or not
    else
      sessionStorage.setItem("openLeftPanelInsights", false);


    //const panel = document.getElementById('right-collapsible-panel');
    const odaIframe = document.querySelector('.oda-chat-widget');

    let showRightPanel = sessionStorage.getItem("openRightPanelInsights");
    console.log("resizeChatBotOnHistoryIcon -> Right panel is  " + showRightPanel);

    if (odaIframe && showLeftPanel) { // If left panel is expanded

      if (showRightPanel === 'true') {  //If left panel is expanded, and right panel is also expanded
        console.log("left panel -> expanded and right panel -> collapsed");

        odaIframe.style.setProperty('width', '52vw', 'important');
        odaIframe.style.setProperty('left', '24vw', 'important');
        //odaIframe.style.setProperty('--widget-max-width', '76vh', 'important');
      }
      else { //If left panel is expanded, and right panel is collapsed
        console.log("left panel -> collapsed and right panel -> collapsed");

        odaIframe.style.setProperty('width', '76vw', 'important');
        odaIframe.style.setProperty('left', '24vw', 'important');
        // odaIframe.style.setProperty('--widget-max-width', '76vh', 'important');
      }

    }
    else if (odaIframe && !showLeftPanel) { // If left panel is collapsed
      // odaIframe.style.setProperty('left', '10vw', 'important');


      if (showRightPanel === 'true') {
        //If left panel is collapsed, and right panel is also expanded
        odaIframe.style.setProperty('width', '75vw', 'important');
        odaIframe.style.setProperty('left', '1vw', 'important');
      }
      else {
        //If left panel is collapsed, and right panel is collapsed
        odaIframe.style.setProperty('left', '5vw', 'important');
        odaIframe.style.setProperty('width', '90vw', 'important');
      }
    }

    console.log("In hideViewInsightsPanel END");

  };




  /*Code for Left Panel*/

  PageModule.prototype.extractCollapsibleData = function (jsonCollapsible) {

    /*
     jsonCollapsible = JSON.parse(jsonCollapsible);
    */

    console.log("Type of jsonCollapsible:", typeof jsonCollapsible);

    if (!Array.isArray(jsonCollapsible)) {
      console.error("jsonCollapsible is not an array:", jsonCollapsible);
      return { recentArray: [] };
    }


    const recentArray = jsonCollapsible.map((value) => {
      return {
        description: value.title
      }
    });


    console.log("recentArray " + JSON.stringify(recentArray));
    console.log("type of recent array " + typeof recentArray)


    /*
    
      const recentArray = jsonCollapsible.RECENT.map((value) => {
       return{
             description:value
            }
        });
    const freqUsedArr = jsonCollapsible.FREQUENTLY_USED.map((value) => ({
       description: value
    }));
    
    const bookMarkedArr = jsonCollapsible.BOOKED_MARKED.map((value) => ({
       description: value
    }));
    
    const agentActionsArr = jsonCollapsible.AGENT_ACTIONS.map((value) => ({
       description: value
    }));
    
    const structuredCollapsible = {
        RECENT: recentArray,
        FREQUENTLY_USED : freqUsedArr,
        BOOKED_MARKED : bookMarkedArr,
        AGENT_ACTIONS:agentActionsArr
    }
    
    console.log(JSON.parse(JSON.stringify(freqUsedArr)));
    
    console.log(JSON.parse(JSON.stringify(bookMarkedArr)));
    
    console.log(JSON.parse(JSON.stringify(agentActionsArr)));
    */
    return {

      recentArray: recentArray

      /*
      structuredCollapsible: structuredCollapsible,
      freqUsedArr : freqUsedArr,
      bookMarkedArr : bookMarkedArr,
      agentActionsArr : agentActionsArr
  */

    };
  };


  PageModule.prototype.frequentCollapsibleData = function (jsonCollapsible) {

    if (!Array.isArray(jsonCollapsible)) {
      console.error("jsonCollapsible is not an array:", jsonCollapsible);
      return { freqUsedArr: [] };
    }


    const freqUsedArr = jsonCollapsible.map((value) => {
      return {
        description: value.title
      }
    });

    return {

      freqUsedArr: freqUsedArr

    };
  }

  PageModule.prototype.bookmarkCollapsibleData = function (jsonCollapsible) {

    if (!Array.isArray(jsonCollapsible)) {
      console.error("jsonCollapsible is not an array:", jsonCollapsible);
      return { bookMarkedArr: [] };
    }


    const bookMarkedArr = jsonCollapsible.map((value) => {
      return {
        description: value.title
      }
    });
    return {

      bookMarkedArr: bookMarkedArr

    };
  }

  PageModule.prototype.agentactionsCollapsibleData = function (jsonCollapsible) {


    if (!Array.isArray(jsonCollapsible)) {
      console.error("jsonCollapsible is not an array:", jsonCollapsible);
      return { agentActionsArr: [] };
    }


    const agentActionsArr = jsonCollapsible.map((value) => {
      return {
        description: value.title
      }
    });
    console.log("agentActionsArr - " + agentActionsArr)

    return {

      agentActionsArr: agentActionsArr

    };
  };






  return PageModule;
});