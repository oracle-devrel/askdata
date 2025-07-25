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

  class isAuthorizedActionChain extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $application, $constants, $variables, $functions } = context;

      const authorized = await $functions.isAuthorized('askdata_nl2sql_admin', $application.user.roles, $variables.baseUrl);

      $variables.isAuthorized = authorized;
    }
  }

  return isAuthorizedActionChain;
});
