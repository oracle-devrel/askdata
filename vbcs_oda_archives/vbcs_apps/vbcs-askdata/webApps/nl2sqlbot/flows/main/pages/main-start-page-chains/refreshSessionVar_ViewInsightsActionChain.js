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

  class refreshSessionVar_ViewInsightsActionChain extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {{payload:any}} params.event 
     * @param {any} params.calledFrom 
     */
    async run(context, { event, calledFrom }) {
      const { $page, $flow, $application, $constants, $variables } = context;

      if (calledFrom === 'autoInsights') {

        await Actions.resetVariables(context, {
          variables: [
    '$page.variables.viewInsightsResponse',
  ],
        });
      } else {
        await Actions.resetVariables(context, {
          variables: [
    '$page.variables.viewInsightsText',
    '$page.variables.viewInsightsResponse',
  ],
        });
      }

       document.getElementById('htmlContainer').innerHTML = ''; // clearing viewinsights response
      console.log("refreshSessionVar_ViewInsightsActionChain payload session: " + event.payload);
      $application.variables.getDetailedInsights = event.payload;

    }
  }

  return refreshSessionVar_ViewInsightsActionChain;
});
