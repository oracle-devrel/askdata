/**  Copyright (c) 2021, 2025 Oracle and/or its affiliates.
* Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
*/

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
