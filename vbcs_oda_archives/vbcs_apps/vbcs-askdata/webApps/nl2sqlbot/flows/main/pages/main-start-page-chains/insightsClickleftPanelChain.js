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

  class insightsClickleftPanelChain extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;



      let showRightPanel1 = sessionStorage.getItem("openRightPanelInsights");

      $variables.showLeftPanel = false;


      // $variables.showLeftPanel = !$variables.showLeftPanel;

      // if (showRightPanel1 && $variables.showLeftPanel) {
      //   $variables.showLeftPanel = true;
      //   console.log("11=> Right panel is  " + showRightPanel1 + " so making LEFT panel: " + $variables.showLeftPanel);
      // } else
      //   if (showRightPanel1) {
      //     $variables.showLeftPanel = false;
      //     console.log("11=> Right panel is  " + showRightPanel1 + " so making LEFT panel: " + $variables.showLeftPanel);
      //   }


      await $functions.resizeChatBotOnHistoryIcon($variables.showLeftPanel);
    }
  }

  return insightsClickleftPanelChain;
});
