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

  class fetchConversationsEventListener extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {{payload:any}} params.event
     */
    async run(context, { event }) {
      const { $page, $flow, $application, $constants, $variables } = context;

      await Actions.callChain(context, {
        chain: 'vbEnter_FetchLeftPanel',
      });
    }
  }

  return fetchConversationsEventListener;
});
