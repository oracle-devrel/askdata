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

  class HyperlinkClickChain extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {number} params.id 
     * @param {string} params.question 
     */
    async run(context, { id, question }) {
      const { $page, $flow, $application, $constants, $variables } = context;

      $variables.lastClickedLinkId = id - 1;
      console.log("lastClickedLinkId is:"+$variables.lastClickedLinkId);

      $page.variables.viewInsightsResponse = $variables.insightsHistory[id-1].answer;
      $variables.htmlResponseInsights = $variables.insightsHistory[id-1].answer;

      document.getElementById('htmlContainer').innerHTML = $variables.insightsHistory[id-1].answer;

      document.getElementById('insights-loader').style.display = 'none';
    }
  }

  return HyperlinkClickChain;
});
