define(['WebSDK'], function (WebSDK) {
  'use strict';

  let eventHelper;
  let socket; // For Auto-Suggestions
  let currentTypedText;  // For Auto-Suggestions

  const PageModule = function PageModule(context) {
    eventHelper = context.getEventHelper();
  };

  function getUri() {
    return "<your-oda-instance>";
  }

  function getChannelId() {
    return "<your-channel-id>"; 
  }

  let isClientAuthEnabled = false;


  // Initialize bot
  PageModule.prototype.init = function (fullname, application, role) {
    console.log("Initializing bot..." + fullname);
    console.log("Initializing role..." + JSON.stringify(role));
    const finalRoles = role.filter(item => item !== "approle.authenticated.user").join(" | ");
    console.log("finalRoles: "+ finalRoles); // Output: "UserAccess"

    const chatSettings = {
      URI: getUri(),
      clientAuthEnabled: isClientAuthEnabled,     // Enables client auth enabled mode of connection if set true, no need to pass if set false
      channelId: getChannelId(),
      /* START CUSTOMIZATION FOR DEMO*/
      //delegate: _delegateObject,
      disablePastActions: 'none',
      enableDraggableButton: true,
      initUserProfile: { profile: { firstName: application.user.username, lastName: 'Doe', email: 'john.doe@oracle.com', timezoneOffset: (new Date()).getTimezoneOffset() * 60 * 1000, properties: { browserLanguage: navigator.language, uiUserToken: application.variables.idcsToken, uiUserId: application.user.username, uiGroupName: finalRoles } } },
      height: '1100px',
      width: '800px',
      //height: '100vh', //layout modification property
      //width: '50vw',  //layout modification property
      //linkHandler: { target: 'background_frame' },
      webViewConfig: { referrerPolicy: 'no-referrer-when-downgrade', closeButtonType: 'label', closeButtonLabel: 'Close', size: 'full', title: 'Ask Oracle' },
      /* END CUSTOMIZATION FOR DEMO*/
      enableAutocomplete: true,                   // Enables autocomplete suggestions on user input
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
          chatTitle: "Web SDK"
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

    // Setup input listener after SDK is initialized
    setupInputListener();
    setupSendButtonListener();
    setupWebSocket(application);


    setTimeout(() => {
      window.Bots = new WebSDK(chatSettings);
      window.Bots.connect().then(() => {
        console.log("Connection Successful");
      }, (reason) => {
        console.log("Connection failed");
        console.log(reason);
      });
    }, 0);
  };

  // For Auto-Suggestions in the 

  function setupSendButtonListener() {
    const sendButton = document.evaluate(
      '/html/body/div[1]/div/div[3]/div/div/button',
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


  function setupInputListener() {
    const textarea = document.evaluate(
      '//*[@id="oda-chat-user-text-input"]',
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null
    ).singleNodeValue;

    if (textarea) {
      textarea.addEventListener('input', handleInput);
    } else {
      console.error('Textarea not found');



      setTimeout(setupInputListener, 1000);
    }
  }

  function handleInput(event) {
    const words = event.target.value.trim().split(/\s+/);
    if (words.length >= 3) {
      sendInputToServer(event.target.value);
    } else {
      hideSuggestionContainer();
    }
  }

  function sendInputToServer(input) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      console.log(JSON.stringify({ InputToSocketAPI: input }));
      socket.send(JSON.stringify({ message: input }));
      currentTypedText = input;
    }
  }


  function setupWebSocket(application) {
    const token = application.variables.idcsToken;

    socket = new WebSocket(`wss://<your-websocket-ip>.sslip.io:8004/wss/suggestions?token=${token}`);

    socket.onopen = function () {
      console.log('WebSocket connection established !!!!!!!!');

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
      console.log('WebSocket connection closed:', event.code, event.reason);
      // Attempt to reconnect after a delay
      setTimeout(setupWebSocket, 5000);
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
    var suggestionContainer = document.getElementById('oda-chat-suggestions-list');
    if (suggestionContainer) {
      suggestionContainer.style.display = 'none';
      suggestionContainer.innerHTML = '';
    }
  }




  return PageModule;
});