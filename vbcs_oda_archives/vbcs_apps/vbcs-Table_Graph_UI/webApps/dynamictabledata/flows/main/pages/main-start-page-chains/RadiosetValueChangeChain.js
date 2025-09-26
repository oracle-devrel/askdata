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

  class RadiosetValueChangeChain extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {any} params.value 
     */
    async run(context, { value }) {
      const { $event, $page, $flow, $application, $variables, $functions } = context;
      const newChartType = value;
      $variables.dynamicChartType = newChartType;
      const isPieOrFunnel = newChartType === 'pie' || newChartType === 'funnel';

      if (isPieOrFunnel && !$variables.hasSwappedChartData && $page.variables.rawChartData) {
        $page.variables.swappedChartDataCache = $functions.transformChartData(
          $page.variables.rawChartData,
          'pie'
        );
        $variables.hasSwappedChartData = true;
      }
      const appropriateData = isPieOrFunnel ? $page.variables.swappedChartDataCache : $page.variables.regularChartDataCache;
      $page.variables.chartDataProvider = null;
      await new Promise(resolve => setTimeout(resolve, 50));
      const arrayDataProvider = await $functions.createChartDataProvider(appropriateData);
      $page.variables.chartDataProvider = arrayDataProvider;
      
      const dynamicChart = document.getElementById('dynamicChart');
      if (dynamicChart) {
        setTimeout(() => dynamicChart.refresh(), 100);
      }
    }
  }
  return RadiosetValueChangeChain;
});