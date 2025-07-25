define(['WebSDK'], function (WebSDK) {
  'use strict';
  var eventHelper;

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
  PageModule.prototype.init = function (fullname, application) {
    console.log("Initializing bot..." + fullname);

    const chatSettings = {
         URI: getUri(),
         clientAuthEnabled: isClientAuthEnabled,     // Enables client auth enabled mode of connection if set true, no need to pass if set false
         channelId: getChannelId(),
         /* START CUSTOMIZATION FOR DEMO*/
         //delegate: _delegateObject,
         disablePastActions: 'none',
         enableDraggableButton: true,
         initUserProfile : {profile:{ firstName: application.user.username, lastName: 'Doe', email: 'john.doe@example.com', timezoneOffset: (new Date()).getTimezoneOffset()*60*1000,properties: { browserLanguage: navigator.language, uiUserToken: application.variables.idcsToken, uiUserId: application.user.username} } },
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
         ttsVoice: [{lang: 'en-us'}],
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
		 ,actionsLayout: 'horizontal'
		 ,cardActionsLayout: 'horizontal'
		 ,formActionsLayout: 'horizontal'
		 ,globalActionsLayout: 'horizontal'
		 ,customHeaderElementId: 'customMenu'
     //,openLinksInNewWindow: true
     ,linkHandler: { target: 'oda-chat-webview' }
		 //,enableResizableWidget: true
		 //,customHeaderElementId: 'customMenu'
		 //,enableEndConversation: false
		 //displayActionAsPills: true,
		 //showTypingIndicator: true,
		 //enableDefaultClientResponse: true,
		 //enableSendTypingStatus: true
      };


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

  return PageModule;
});