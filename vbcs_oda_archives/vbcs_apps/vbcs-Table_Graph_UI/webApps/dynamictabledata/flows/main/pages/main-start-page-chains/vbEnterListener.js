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
      const { $page, $flow, $application, $constants, $variables, $functions, $chain } = context;

      const resultGraphData = await $functions.getBarChartData();

      $page.variables.graphBARDataADP.data = resultGraphData.usageGraphData;
      $variables.xAxisLabel =resultGraphData.xAxisLabel;
      $variables.yAxisLabel = resultGraphData.yAxisLabel;
      $variables.titleText = resultGraphData.titleText; 
      $variables.showLegend = resultGraphData.showLegend;  
      $variables.tooltipRenderer = resultGraphData.tooltipRenderer;  

      const lookupQueryParam = await $functions.lookupQueryParam('idataId');

       const lookupQueryParam1 = await $functions.lookupQueryParam('igraphId');
     
      $variables.inputDataId = lookupQueryParam;
      $variables.graphId = lookupQueryParam1;

      const responseGetData = await Actions.callRest(context, {
        endpoint: 'interactiveTables/getGetdata',
        uriParams: {
          "idataId": $page.variables.inputDataId,
          "userId": $application.user.email
        },
      });
     
      const dataProvider = await $functions.getTableDataFromJSON(responseGetData.body);
      $variables.myPDP = dataProvider;
    }
  }

  return vbEnterListener;
});
