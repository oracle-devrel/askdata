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

  class getDetailedInsightsButtonActionChain extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables } = context;
      sessionStorage.setItem("openRightPanelInsights", true); // created this to handle whether right panel is opened or not
      sessionStorage.setItem("idataIdSession", $page.variables.inputDataId);
      sessionStorage.setItem("getDetailedInsights", true);
      

      window.top.postMessage({ action: 'getDetailedInsights', idataId: $page.variables.inputDataId, calledFrom: 'getDetailedInsights' }, '*');

    }
  }

  return getDetailedInsightsButtonActionChain;
});
