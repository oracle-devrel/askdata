define([
  'vb/action/actionChain',
  'vb/action/actions',
  'vb/action/actionUtils',
], (
  ActionChain,
  Actions,
  ActionUtils
) => {
  'use strict';

  class vbEnter_FetchLeftPanel extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;
/*
      let responseString = $application.variables.sideNavData;
      let response = typeof responseString === 'string' ? JSON.parse(responseString) : responseString;

      console.log("response: " + JSON.stringify(response));
      let transformedData = {
        RECENT: response.RECENT.map(item => ({ label: item })),
        FREQUENTLY_USED: response.FREQUENTLY_USED.map(item => ({ label: item })),
        BOOKED_MARKED: response.BOOKED_MARKED.map(item => ({ label: item })),
        AGENT_ACTIONS: response.AGENT_ACTIONS.map(item => ({ label: item }))
      };

     console.log("transformedData: " + JSON.stringify(transformedData));

      $page.variables.leftPanelCollapsibleData = transformedData;
      */
     $variables.userId = $application.variables.webUserName;
    console.log("userId -"+$page.variables.userId);

    

      const frequentResponse = await Actions.callRest(context, {
        endpoint: 'Recent/getFrequent',
        uriParams: {
          userId: $variables.userId,
        },
        responseBodyFormat: 'json',
      });
console.log("JSON Frequent of table--" + JSON.stringify(frequentResponse.body));
      const bookmarkResponse = await Actions.callRest(context, {
        endpoint: 'Recent/getBookmarks',
        responseBodyFormat: 'json',
        uriParams: {
          userId: $variables.userId,
        },
      });
console.log("JSON Bookmark of table--" + JSON.stringify(bookmarkResponse.body));
      const agentResponse = await Actions.callRest(context, {
        endpoint: 'AgentActions/getActions',
        uriParams: {
          userId: $variables.userId,
        },
        responseBodyFormat: 'json',
      });
        const recentResponse = await Actions.callRest(context, {
        endpoint: 'Recent/getRecent',
        uriParams: {
          userId: $variables.userId,
        },
        responseBodyFormat: 'json',
      });
console.log("JSON Recent of table--" + JSON.stringify(recentResponse.body));
console.log("JSON Agent Actions of table--" + JSON.stringify(agentResponse.body));

      
     

      const frequentCollapsibleData = await $functions.frequentCollapsibleData(frequentResponse.body);
   
      const bookmarkCollapsibleData = await $functions.bookmarkCollapsibleData(bookmarkResponse.body);

      const agentactionsCollapsibleData = await $functions.agentactionsCollapsibleData(agentResponse.body);
      
       const resultCollapsible = await $functions.extractCollapsibleData(recentResponse.body);

      $page.variables.recentArr = resultCollapsible.recentArray;
       $page.variables.freqUsedArr = frequentCollapsibleData.freqUsedArr;
       $page.variables.bookMarkedArr = bookmarkCollapsibleData.bookMarkedArr;
       $page.variables.agentActionsArr = agentactionsCollapsibleData.agentActionsArr;


    }
  }

  return vbEnter_FetchLeftPanel;
});
