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

  class autoInsights_ServiceCallListener extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {object} params.event 
     */
    async run(context, { event }) {
      const { $page, $flow, $application, $constants, $variables } = context;

      $variables.viewInsightsText = 'Get Insights for the current Dataset';

      await Actions.callChain(context, {
        chain: 'viewInsightsSendButtonAction',
      });

      await Actions.resetVariables(context, {
        variables: [
    '$page.variables.viewInsightsText',
  ],
      });

      $variables.insightsHistory.pop();
    }
  }

  return autoInsights_ServiceCallListener;
});
