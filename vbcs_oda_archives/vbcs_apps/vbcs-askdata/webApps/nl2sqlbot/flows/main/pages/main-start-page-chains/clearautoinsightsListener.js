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

  class clearautoinsightsListener extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables } = context;

      await Actions.resetVariables(context, {
        variables: [
    '$page.variables.insightsHistory',
    '$page.variables.insightsHistory.answer',
    '$page.variables.insightsHistory.idataID',
    '$page.variables.insightsHistory.question',
  ],
      });
    }
  }

  return clearautoinsightsListener;
});
