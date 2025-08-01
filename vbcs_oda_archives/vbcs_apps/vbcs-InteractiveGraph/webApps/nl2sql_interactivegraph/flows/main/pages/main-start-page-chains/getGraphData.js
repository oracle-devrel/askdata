/**  Copyright (c) 2021, 2025 Oracle and/or its affiliates.
* Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
*/

/* global Plotly */
define([
  'vb/action/actionChain',
  'vb/action/actions',
  'vb/action/actionUtils',
  'https://cdn.plot.ly/plotly-latest.min.js'
], (
  ActionChain,
  Actions,
  ActionUtils,
  Plotly
) => {
  'use strict';

  class getGraphData extends ActionChain {
    /**  
     * @param {Object} context
     */
    async run(context) {
      const { $page, $flow, $application, $constants, $variables } = context;
      const urlParams = new URLSearchParams(window.location.search);
      const queryParamsForApi = {
        graphId: urlParams.get('graphId')
      };

      const response = await Actions.callRest(context, {
        endpoint: 'interactive-graph/getIgraph',
        method: 'GET',
        queryParams: queryParamsForApi
      });

      console.log("Full API Response:", response);
      console.log("Layout:", JSON.stringify(response.body.layout));

      // Check if Plotly is defined after loading
      if (typeof Plotly === 'undefined') {
        console.error("Plotly failed to load.");
        return; 
      }

      var config = {
        showLink: false,
        plotlyServerURL: "http://<plotly-server>:8050/",
        displaylogo: false,
        responsive: true
        };

      // Plotting
      if (response && response.body.data) {
        Plotly.newPlot('plotlyGraph', response.body.data, response.body.layout, config);
      } else {
        console.error("Data not found in the response");
      }
    }
  }
  return getGraphData;
});
