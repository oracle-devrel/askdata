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
      const idataId = await $functions.lookupQueryParam('idataId');
      const igraphId = await $functions.lookupQueryParam('igraphId');
      const pPrompt = await $functions.lookupQueryParam('pPrompt');
     
      $variables.inputDataId = idataId;
      $variables.graphId = igraphId;
      $variables.pPrompt = pPrompt;

      const responseGetData = await Actions.callRest(context, {
        endpoint: 'interactiveTables/getGetdata',
        uriParams: {
          "idataId": $page.variables.inputDataId
      },
      });

      const rawData = responseGetData.body;
      $variables.exportExcelDataProvider = rawData; 
     
      const dataProvider = await $functions.getTableDataFromJSON(responseGetData.body);
      $variables.myPDP = dataProvider;

      const dynamicChartResponse = await Actions.callRest(context, {
        endpoint: 'interactiveTables/postGetojet',
        body: {
          idataId: $page.variables.inputDataId,
          graphType: '',
          xAxis: '',
          yAxis: '',
          groupBy: '',
        },
      });

      $page.variables.rawChartData = dynamicChartResponse.body.data;
      $variables.dynamicChartType = dynamicChartResponse.body.chartType;
      $variables.dynamicChartDescription = dynamicChartResponse.body.chartDesc;
      $variables.xAxisLabel = dynamicChartResponse.body.xLabel;
      $variables.yAxisLabel = dynamicChartResponse.body.yLabel;

      const isPieOrFunnel = $variables.dynamicChartType === 'pie' || $variables.dynamicChartType === 'funnel';

      const regularChartData = $functions.transformChartData(
        dynamicChartResponse.body.data,
        'bar'
      );

      let pieOrFunnelChartData = [];
      if (isPieOrFunnel) {
        pieOrFunnelChartData = $functions.transformChartData(
          dynamicChartResponse.body.data,
          'pie'
        );
      }

      $page.variables.regularChartDataCache = regularChartData;
      $page.variables.swappedChartDataCache = pieOrFunnelChartData;
      $variables.hasSwappedChartData = isPieOrFunnel;

      const hasXY = regularChartData.some(item => item.x !== undefined && item.y !== undefined);
      $page.variables.isXYAvailable = hasXY;
      
      const appropriateData = isPieOrFunnel ? pieOrFunnelChartData : regularChartData;
      const arrayDataProvider = await $functions.createChartDataProvider(appropriateData);
      $page.variables.chartDataProvider = arrayDataProvider;

      $page.variables.lastSearchPrompt = $page.variables.iPrompt;

      setTimeout(() => {
        const collapsible = document.getElementById('graphCollapsible');
        if (collapsible) {
          collapsible.expanded = true;
        }
      }, 100);
    }
  }
  return vbEnterListener;
});
