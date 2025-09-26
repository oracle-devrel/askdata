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

  class leftCollapsibleCollapseChain extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {any} params.event 
     */
    async run(context, { event = sdsd }) {
      const { $page, $flow, $application, $constants, $variables, $event } = context;

      
     //if ($event.currentTarget.id === 'collapsible-panel') {
        $variables.showLeftPanel = false;
      //}
    }
  }

  return leftCollapsibleCollapseChain;
});
