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

  class hyperlinkClickChain extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {string} params.label 
     * @param {number} params.id 
     */
    async run(context, { label, id }) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;
      const busyContext = oj.Context.getPageContext().getBusyContext();
      const options = {"description": "Processing request..."};
      const resolve = busyContext.addBusyState(options);
      console.log("label is:"+label)
      console.log("id is:"+id)
      $variables.lastClickedLinkId = id - 1;
      console.log("lastClickedLinkId is:"+$variables.lastClickedLinkId)
      try{
        $variables.loadingMessage = "";
        $variables.isLoading = true;
        $variables.isGraphLoading = true;
        $variables.regularChartDataCache = [];
        $variables.swappedChartDataCache = [];
        $variables.iDataStepNumber = id;

        const responseIPrompt = await Actions.callRest(context, {
          endpoint: 'interactiveTables/getIpromptData',
          uriParams: {
          "idataId": $page.variables.inputDataId,
          "stepNumber": $page.variables.iDataStepNumber
          }
        });

        const rawData = responseIPrompt.body.tabData;
        $page.variables.exportExcelDataProvider = rawData;
        if (rawData.length > 0) {
          const newColumns = Object.keys(rawData[0]).map(key => ({
            headerText: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            field: key
          }));
          $page.variables.tableColumns = newColumns;
        } else {
          $page.variables.tableColumns = [];
        }

        $page.variables.myPDP = null;
        await new Promise(resolve => setTimeout(resolve, 50));
        const newData = await $functions.getTableDataFromJSON(rawData);
        $page.variables.myPDP = newData;

        const dynamicTable = document.getElementById('dynamicTable');
        if (dynamicTable) {
          setTimeout(() => dynamicTable.refresh(), 100);
        }

        // const rawData = responseIPrompt.body.tabData;
        // if (rawData.length > 0) {
        //   $page.variables.exportExcelDataProvider = rawData;
        //   const newColumns = Object.keys(rawData[0]).map(key => ({
        //     headerText: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        //     field: key
        //   }));
        //   $page.variables.tableColumns = newColumns;
        //   $page.variables.myPDP = null;
        //   await new Promise(resolve => setTimeout(resolve, 50));
        //   const newData = await $functions.getTableDataFromJSON(rawData);
        //   $page.variables.myPDP = newData;
        //   const dynamicTable = document.getElementById('dynamicTable');
        //   if (dynamicTable) {
        //     setTimeout(() => dynamicTable.refresh(), 100);
        //   }
        // }

        $page.variables.iPromptResponseMessage = responseIPrompt.body.response;
        // Setting chart data
        $page.variables.rawChartData = responseIPrompt.body.chartData;
        $variables.dynamicChartType = responseIPrompt.body.chartType;
        $variables.dynamicChartDescription = responseIPrompt.body.chartDesc;
        $variables.xAxisLabel = responseIPrompt.body.xLabel;
        $variables.yAxisLabel = responseIPrompt.body.yLabel;
        const isPieOrFunnel = $variables.dynamicChartType === 'pie' || $variables.dynamicChartType === 'funnel';
        const regularChartData = $functions.transformChartData(
          responseIPrompt.body.chartData,
          'bar'
        );

        let pieOrFunnelChartData = [];
        if (isPieOrFunnel) {
          pieOrFunnelChartData = $functions.transformChartData(
          responseIPrompt.body.chartData,
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
        $variables.isLoading = false;
        $variables.isGraphLoading = false;
        $variables.loadingMessage = "";
        $variables.lastClickedLinkId = id - 1;
        resolve();
      }
    }
  }
  return hyperlinkClickChain;
});
