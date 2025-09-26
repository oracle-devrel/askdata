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

  class ulClickChain extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {any} params.input 
     */
    async run(context, { input }) {
      const { $page, $flow, $application, $constants, $variables } = context;

      await Actions.fireNotificationEvent(context, {
        summary: input,
      });
    }
  }

  return ulClickChain;
});
