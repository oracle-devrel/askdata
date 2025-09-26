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

  class autoInsightsButtonActionChain extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables } = context;
      sessionStorage.setItem("openRightPanelInsights", true);
      console.log("session storage -",sessionStorage.getItem("openRightPanelInsights"));
      sessionStorage.setItem("getDetailedInsights", false); // true for getDetailedInsights

      sessionStorage.setItem("idataIdSession", $page.variables.inputDataId);

      window.top.postMessage({ action: 'autoInsights', idataId: $page.variables.inputDataId, calledFrom: 'autoInsights' }, '*');

    }
  }

  return autoInsightsButtonActionChain;
});
