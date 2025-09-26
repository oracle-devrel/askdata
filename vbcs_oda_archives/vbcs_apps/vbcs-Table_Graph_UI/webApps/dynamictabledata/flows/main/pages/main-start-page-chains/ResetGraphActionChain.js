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

  class ResetGraphActionChain extends ActionChain {

    /**
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;
      const busyContext = oj.Context.getPageContext().getBusyContext();
      const options = {"description": "Processing request..."};
      const resolve = busyContext.addBusyState(options);

      try{
        $variables.loadingMessage = "";
        $variables.isGraphLoading = true;
        $variables.regularChartDataCache = [];
        $variables.swappedChartDataCache = [];
        
        const responseIGraphPrompt = await Actions.callRest(context, {
          endpoint: 'interactiveTables/postIpromptGraph',
          responseBodyFormat: 'json',
          body: {
            iGraphPrompt: 'RESET',
            idataId: $page.variables.inputDataId,
            stepNumber: $page.variables.iDataStepNumber
          },
        });

        $page.variables.iGraphPrompt = '';
        $page.variables.rawChartData = responseIGraphPrompt.body.chartData;
        $variables.dynamicChartType = responseIGraphPrompt.body.chartType;
        $variables.dynamicChartDescription = responseIGraphPrompt.body.chartDesc;
        $variables.xAxisLabel = responseIGraphPrompt.body.xLabel;
        $variables.yAxisLabel = responseIGraphPrompt.body.yLabel;

        const isPieOrFunnel = $variables.dynamicChartType === 'pie' || $variables.dynamicChartType === 'funnel';

        const regularChartData = $functions.transformChartData(
          responseIGraphPrompt.body.chartData,
          'bar'
        );

        let pieOrFunnelChartData = [];
        if (isPieOrFunnel) {
          pieOrFunnelChartData = $functions.transformChartData(
          responseIGraphPrompt.body.chartData,
          'pie' 
          );
        }

        $variables.regularChartDataCache = regularChartData;
        $variables.swappedChartDataCache = pieOrFunnelChartData;
        $variables.hasSwappedChartData = isPieOrFunnel;

        const hasXY = regularChartData.some(item => item.x !== undefined && item.y !== undefined);
        $page.variables.isXYAvailable = hasXY;

        $page.variables.chartDataProvider = null;
        await new Promise(resolve => setTimeout(resolve, 50));

        const appropriateData = isPieOrFunnel ? pieOrFunnelChartData : regularChartData;
        const arrayDataProvider = await $functions.createChartDataProvider(appropriateData);
        $page.variables.chartDataProvider = arrayDataProvider;

      } finally {
        $variables.isGraphLoading = false;
        $variables.loadingMessage = "";
        resolve();
    }
  }
  }
  return ResetGraphActionChain;
});
