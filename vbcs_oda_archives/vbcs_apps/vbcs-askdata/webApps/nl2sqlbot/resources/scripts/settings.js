'use strict';

/**
 * Set client auth mode - true to enable client auth, false to disable it.
 *
 * Disabling authentication is preferred for initial integration of the SDK with the web app.
 *
 * When client authentication has been disabled, only connections made from unblocked lists (allowed domains) are
 * allowed at the server. This use case is recommended when the client application cannot generate a signed JWT (because
 * of a static website or no authentication mechanism for the web/mobile app) but requires ODA integration. It can also
 * be used when the chat widget is already secured and visible to only authenticated users in the client platforms (web
 * application with the protected page).
 *
 * For other cases, it is recommended that client auth enabled mode is used when using the SDK for production as it adds
 * another layer of security when connecting to a DA/skill.
 *
 * When client authentication has been enabled, client authentication is enforced by signed JWT tokens in addition to
 * the unblocked lists. When the SDK needs to establish a connection with the ODA server, it first requests a JWT token
 * from the client and then sends it along with the connection request. The ODA server validates the token signature and
 * obtains the claim set from the JWT payload to verify the token to establish the connection.
 *
 * The Web channel in ODA must also be enabled to accept client auth enabled connections.
 */
var isClientAuthEnabled = false;
var socket;
var currentTypedText;




/*window.onkeypress = function(e) {
   var messageField = document.getElementsByClassName('oda-chat-user-input oda-chat-user-input-inline-send');
   if (messageField[0].value.length == 0 && e.key === " " || e.key === "Spacebar") {
      e.preventDefault();
      var micbutton = document.getElementsByClassName('oda-chat-icon oda-chat-footer-button oda-chat-flex oda-chat-button-switch-voice');
      micbutton[0].click();
   }
}*/

function setupWebSocket() {
  socket = new WebSocket('wss://207.211.161.208.sslip.io:8004/ws/suggestions');

  socket.onopen = function () {
    console.log('WebSocket connection established');
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

function setupSendButtonListener() {
  const sendButton = document.evaluate(
    '/html/body/div[4]/div/div[3]/div/div/button',
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
    bottom: `${window.innerHeight - inputRect.top - 52}px`,
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

/*
var _delegateObject = {
    beforeDisplay(message) {
        if (message.messagePayload.type == 'text' && message.messagePayload.actions.length == 3 && message.messagePayload.actions[0].postback.target == 'SystemIntentsRoutingAction.cancel'){

        //remove last button
        message.messagePayload.actions.pop();

      }
        console.log('beforeDisplay: ' + JSON.stringify(message));

        // Handle custom channel extensions
         
        if (message.messagePayload.type == 'text' && message.messagePayload.channelExtensions && message.messagePayload.channelExtensions.alert) {
            //print the message
            alert(message.messagePayload.channelExtensions.alert);
        }

        // User session time-out reminder
        
        resetTimer();  //all messages reset the timer

        if (message.messagePayload.channelExtensions) {
          if (message.messagePayload.channelExtensions.lastState) {
            //ONLY RESPONSES WITH A LAST STATE PROPERTY SET THE TIMER
            setTimer(message.messagePayload.channelExtensions.lastState,
            message.messagePayload.channelExtensions.botId,
            message.messagePayload.channelExtensions.goToState);
          }
        }

        // split long text messages
        
        if (message.messagePayload.type == 'text') {
            message.messagePayload.text = splitParagraph(message.messagePayload.text);
        }

        //
         // Handling System.Webview component.
         // 1. webview components are rendered as cards layout with single card
         // 2. url contains ODA host URL and /webviews/
         //
        if (message.messagePayload.cards) {

            //cards must have at least a single action. So its save to access the
            //first card directly
            if (message.messagePayload.cards[0].actions[0].url.includes('/connectors/v2/webviews/')) {
                //change type "url" to type "webview". This then renders the webview in the
                //messenger's iFrame, not relying on "linkHandler" property to point to the
                //embedded iFrame
                message.messagePayload.cards[0].actions[0].type = "webview";
            }
        }
        return message;
    },
    beforeSend(message) {
        return message;
    },
    beforePostbackSend(postback) {
        return postback;
    }
} */

/*
function showHideParagraphs(lidx) {
    var dots = document.getElementById("dots" + lidx);
    var moreText = document.getElementById("more" + lidx);
    var btnText = document.getElementById("myBtn" + lidx);
    if (dots.style.display === "none") {
        dots.style.display = "inline";
        btnText.innerHTML = "Read more";
        moreText.style.display = "none";
    } else {
        dots.style.display = "none";
        btnText.innerHTML = "Read less";
        moreText.style.display = "inline";
    }
}

var gidx = 0;

function splitParagraph(txt) {
    var paragraphs = txt.split("\n\n");
    console.log(paragraphs);
    if (paragraphs.length > 1) {
        var html = "<p>"+paragraphs[0]+'<span id="dots'+gidx+'">...</span></p><span id="more'+gidx+'"class="more">';
        for (var idx = 1; idx < paragraphs.length; idx++) {
            html += "<p>" + paragraphs[idx] + "</p>";
        }
        html += '</span><button class="readMore" onclick="showHideParagraphs('+gidx+')" id="myBtn'+gidx+'">Read more</button>';
        gidx++;
        return html;
    } else
        return txt;
} */
/**
 * Initializes the SDK and sets a global field with passed name for it the can
 * be referred later
 *
 * @param {string} name Name by which the chat widget should be referred
 */
function initSdk(name) {
  // Retry initialization later if the web page hasn't finished loading or the WebSDK is not available yet
  if (!document || !document.body || !WebSDK) {
    setTimeout(function () {
      //Bots.setDelegate(_delegateObject);
      initSdk(name);
    }, 2000);
    return;
  }

  if (!name) {
    name = 'Bots';          // Set default reference name to 'Bots'
  }
  var Bots;
  setTimeout(function () {



    // fetch user name from session

    //sessionStorage.setItem("username: ", $application.variables.currentuser);

    

    // document.addEventListener("DOMContentLoaded", function () {
    //   const username = sessionStorage.getItem('username');
    //   console.log("in the settings file -> username: " + username);
     
    // });

    let user = "";

    document.addEventListener("DOMContentLoaded", function() {
    window.addEventListener('usernameSet', function(event) {

      user = event.detail.username;

        console.log("in the settings file -> username: " + event.detail.username);
        // Use the username as needed
    });
});




// // Ensure the variable is declared correctly.
// let loggedInUserName = ""; // Declare the variable before using it.

// // Now, retrieve the username from the body tag data attribute
// loggedInUserName = document.body.getAttribute('data-username');

// if (loggedInUserName) {
//     console.log('Username!!! in settings.js: ' + loggedInUserName);
//     // You can now use loggedInUserName for ODA integration or other purposes
// } else {
//     console.log('Username!!! not found');
// }





    /**
    * SDK configuration settings
    *
    * Other than URI, all fields are optional with two exceptions for auth modes:
    *
    * In client auth disabled mode, 'channelId' must be passed, 'userId' is optional
    * In client auth enabled mode, 'clientAuthEnabled: true' must be passed
    */
    var chatWidgetSettings = {
      URI: getUri(),
      clientAuthEnabled: isClientAuthEnabled,     // Enables client auth enabled mode of connection if set true, no need to pass if set false
      channelId: getChannelId(),
      /* START CUSTOMIZATION FOR DEMO*/
      //delegate: _delegateObject,
      disablePastActions: 'none',
      enableDraggableButton: true,
      initUserProfile: { profile: { firstName: 'XXXXX', lastName: 'Appees', email: 'bbbbbb@oracle.com', timezoneOffset: (new Date()).getTimezoneOffset() * 60 * 1000, properties: { browserLanguage: navigator.language } } },
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
        logo: 'resources/images/iconMax.png',
        avatarAgent: 'resources/images/iconProfile.png',
        avatarUser: 'resources/images/iconProfile.png',
        avatarBot: 'resources/images/iconMax.png',
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

    // Initialize SDK
    if (isClientAuthEnabled) {
      Bots = new WebSDK(chatWidgetSettings, generateToken);
    } else {
      Bots = new WebSDK(chatWidgetSettings);
    }

    // Connect to skill when the widget is expanded for the first time
    var isFirstConnection = true;
    Bots.on(WebSDK.EVENT.WIDGET_OPENED, function () {
      if (isFirstConnection) {
        Bots.connect();
        isFirstConnection = false;
      }
    });

    function actionHandler(action) {
      Bots.sendMessage(action);
    }

    // Create global object to refer Bots
    window[name] = Bots;
    // Setup input listener after SDK is initialized
    //setupInputListener();
    //setupSendButtonListener();
    //setupWebSocket();
  }, 0);
}

/**
 * Use this same value for the name property in the 
 * token server's routes/config.json file as you
 * use for the APP_NAME.
 */
const APP_NAME = 'webSdkAuth'
const TOKEN_SERVER_ENDPOINT = 'https://axm3taxqtrgepo5eyp3vbhsrly.apigateway.us-chicago-1.oci.customer-oci.com/jwt/token'
/**
 * Function to generate JWT tokens. It returns a Promise to provide tokens.
 * The function is passed to SDK which uses it to fetch token whenever it needs
 * to establish a connection to the chat server. If a user ID isn't passed in, 
 * as in this function, then the token server generates one.
 * @returns {Promise} Promise to provide a signed JWT token
 */
var generateToken = function () {
  return new Promise((resolve) => {
    fetch(TOKEN_SERVER_ENDPOINT +
      '?config=' + APP_NAME).then((
        response) => {
        if (response.status !== 200) {
          console.log(
            'Looks like there was a problem. Status Code: ${response.status}.');
          return;
        }
        // Examine the text in the response
        response.json().then(function (data) {
          resolve(data.token);
        });
      })
  });
}

var timer = null;

function resetTimer() {
  if (timer != null) {
    clearTimeout(timer);
  }
  return;
}

function setTimer(lastState, botId, goToState) {

  var _lastState = lastState;
  var _botId = botId;
  var _goToState = goToState;

  //console.log("...."+_lastState+"....."+_botId+"......"+_goToState);
  timer = setTimeout(() => {
    //send message after max. idle time inactivity
    //console.log("...."+_lastState+"....."+_botId+"......"+_goToState);
    Bots.sendMessage({
      "postback": {
        "variables": { "lastState": _lastState },
        "system.botId": _botId,
        //invokes named action transition on system.state or "next" transition
        "action": "",
        "system.state": _goToState
      },
      "text": "Maximum user idle time reached ...",
      "type": "postback"
    });
  },
    //set to 5 seconds of idle time
    5 * 1000
  );
}

function clear() {
  Bots.sendMessage('clear');
}

function getUri() {
  return "oda-3259ee5123c349feae0c5a062ba9ea97-da6f7264.data.digitalassistant.oci.oraclecloud.com";
}

function getChannelId() {
    return "d81b8968-bf16-4852-84c6-d0ee52e2bef9"
}