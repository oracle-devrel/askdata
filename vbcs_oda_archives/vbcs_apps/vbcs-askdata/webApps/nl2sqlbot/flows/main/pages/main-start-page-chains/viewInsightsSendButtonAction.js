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

  class viewInsightsSendButtonAction extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables } = context;


      document.getElementById('insights-loader').style.display = 'flex';
     // document.getElementById('insights-content').style.display = 'none';


      console.log("from Session viewInsightsSendButtonAction :", sessionStorage.getItem("idataIdSession"));

      let idataId = sessionStorage.getItem("idataIdSession");
      console.log("idataId: " + idataId);

      const response = await Actions.callRest(context, {
        endpoint: 'AgentActions/postSubmit',
        body: {
          idataId: idataId,
          userId: $application.user.email,
          prompt: $page.variables.viewInsightsText,
        },
      });

      if (response.ok) {
        if (true) {
          console.log("response: " + JSON.stringify(response));
          $page.variables.viewInsightsResponse = response.body.message;
          $variables.htmlResponseInsights = response.body.message;

          document.getElementById('htmlContainer').innerHTML = response.body.message;

          document.getElementById('insights-loader').style.display = 'none';

          const history = {
  question: $variables.viewInsightsText,
  answer: response.body.message,
  idataID: idataId,
};

          $variables.insightsHistory.push(history);

          sessionStorage.setItem("insightHistorySession",true);

          $variables.lastClickedLinkId = $variables.insightsHistory.length - 1;

          console.log("history: " + JSON.stringify(history));
          //document.getElementById('insights-content').style.display = 'block';

        }

        return;
      }
    }
  }

  return viewInsightsSendButtonAction;
});
