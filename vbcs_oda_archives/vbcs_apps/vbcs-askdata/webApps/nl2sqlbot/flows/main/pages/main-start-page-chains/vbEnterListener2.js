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

  class vbEnterListener2 extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;

      if ($application.variables.isAuthorized === true) {

        await $functions.init($application.user.username, $application, $application.user.roles);
      }
    }
  }

  return vbEnterListener2;
});
