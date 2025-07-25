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

  class vbEnterListener extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $application, $constants, $variables } = context;

      const response = await Actions.callRest(context, {
        endpoint: 'GetIDCSToken/postToken',
        body: 'scope=urn:opc:idm:__myscopes__&grant_type=client_credentials',
      });

      if (response.ok) {
        $variables.idcsToken = response?.body?.access_token;
      }
    }
  }

  return vbEnterListener;
});
