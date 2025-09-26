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

  class refreshSessionVar_ViewInsightsListener extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {object} params.event 
     */
    async run(context, { event }) {
      const { $page, $flow, $application, $constants, $variables } = context;

      // ---- ASSIGN VARIABLE ---- //
    }
  }

  return refreshSessionVar_ViewInsightsListener;
});
