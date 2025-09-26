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

  class recentPanelClickChain extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {any} params.selectedItem 
     */
    async run(context, { selectedItem = $current.data.description }) {
      const { $page, $flow, $application, $constants, $variables, $context, $functions, $current } = context;

      console.log("selectedItem: "+JSON.stringify(selectedItem));

      await $functions.openBotSendMessage(selectedItem);
    }
  }

  return recentPanelClickChain;
});
