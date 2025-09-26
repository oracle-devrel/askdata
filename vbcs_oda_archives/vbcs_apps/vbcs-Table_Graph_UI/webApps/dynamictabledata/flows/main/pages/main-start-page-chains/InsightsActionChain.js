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

  class InsightsActionChain extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;
      const busyContext = oj.Context.getPageContext().getBusyContext();
      const options = {"description": "Processing request..."};
      const resolve = busyContext.addBusyState(options);
      
      try {
        $variables.loadingMessage = "";
        $variables.isLoading = true;
        
        const responseInsights = await Actions.callRest(context, {
          endpoint: 'interactiveTables/postAgentSubmit',
          responseBodyFormat: 'json',
          body: {
            idataId: $page.variables.inputDataId,
            userId: $application.user.email,
            prompt: "_get_insights"
          },
        });
        
        $page.variables.iPromptResponseMessage = responseInsights.body.message;
        $page.variables.lastSearchPrompt = "Get Insights for the current Dataset";
        $page.variables.iPrompt = '';

      } finally {
        $variables.isLoading = false;
        $variables.loadingMessage = "";
        resolve();
      }
    }
  }
  return InsightsActionChain;
});
