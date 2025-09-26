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

  class switchViewModeChanged extends ActionChain {

    /**
     * @param {Object} context
     * @param {Object} params
     * @param {{oldValue:boolean,value:boolean}} params.event
     */
    async run(context, { event }) {
      const { $page, $flow, $application, $constants, $variables, $functions } = context;
      
      const isGroupView = $page.variables.isGroupView;
      $page.variables.chartViewMode = isGroupView ? "group" : "series";

      // Then continue with the transformation as before
      const chartData = $functions.transformChartData(
        $page.variables.rawChartData, 
        $page.variables.chartViewMode
      );

      // Clear and reset data provider
      $page.variables.chartDataProvider = null;
      await new Promise(resolve => setTimeout(resolve, 50));
      const arrayDataProvider = await $functions.createChartDataProvider(chartData);
      $page.variables.chartDataProvider = arrayDataProvider;
    }
  }

  return switchViewModeChanged;
});
