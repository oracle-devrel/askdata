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

  class ButtonActionChain1 extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables } = context;

      let idataId = sessionStorage.getItem("idataIdSession");

      console.log("idataId: " + idataId);

      const response = await Actions.callRest(context, {
        endpoint: 'AgentActions/postSubmit',
        body: {
          idataId: idataId,
          userId: $application.user.email,
          prompt: 'RESET',
        },
      });

      if (response.ok) {
        if (true) {
          console.log("response: " + JSON.stringify(response));
          $page.variables.viewInsightsResponse = response.body.message;
          $variables.htmlResponseInsights = response.body.message;

          document.getElementById('htmlContainer').innerHTML = response.body.message;

          document.getElementById('insights-loader').style.display = 'none';

          await Actions.resetVariables(context, {
            variables: [
    '$page.variables.viewInsightsResponse',
    '$page.variables.viewInsightsText',
    '$page.variables.insightsHistory',
    '$page.variables.lastClickedLinkId',
  ],
          });
          //document.getElementById('insights-content').style.display = 'block';

        }

        return;
      }
    }

    
  }

  return ButtonActionChain1;
});
