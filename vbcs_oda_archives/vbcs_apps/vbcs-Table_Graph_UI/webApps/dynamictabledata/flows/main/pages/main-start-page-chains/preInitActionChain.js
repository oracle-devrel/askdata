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

  class preInitActionChain extends ActionChain {

    /**
     * @param {Object} context
     * @return {{cancelled:boolean}}
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;
      
      await $functions.extractQueryParams();

      // Navigation to this page can be canceled by returning an object with the property cancelled set to true. This is useful if the user does not have permission to view this page.
      return { cancelled: false };
    }
  }

  return preInitActionChain;
});
