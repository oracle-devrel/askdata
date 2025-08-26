/**  Copyright (c) 2021, 2025 Oracle and/or its affiliates.
* Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
*/

define(['ojs/ojcore', 'ojs/ojtable', 'ojs/ojarraydataprovider', 'ojs/ojpagingdataproviderview','knockout'], (ojcore, ojtable, ArrayDataProvider, PagingDataProviderView, ko) => {
  'use strict';
var PageModule = function PageModule() {};
  const queryParams = {};
  
  PageModule.prototype.extractQueryParams = function() {
    var queryString = window.location.search;

    queryString = queryString.slice(queryString.indexOf('?') + 1);
    const pairs = queryString.split('&');
    console.log("Pairs --"+pairs) ;
    for (var i = 0; i < pairs.length; i++) {
      const [key, value] = pairs[i].split('=');
      queryParams[key] = decodeURIComponent(value);
      console.log("query parms and Key"+  queryParams[key]);
    };
  };
  
  PageModule.prototype.lookupQueryParam = function(name) {
    console.log("query param name"+queryParams[name]);
    return queryParams[name];
    
  };
  
   PageModule.prototype.getSampleChartAxis = function () {
    // Define categories and corresponding series data
    let chartData = [
        {
            "name": "Sales",  // Series name
            "items": [100, 200, 150, 300, 250, 400]  // Values for each category
        },
        {
            "name": "Expenses",  // Another series name
            "items": [80, 180, 120, 250, 220, 350]  // Values for each category
        }
    ];

    // Define the categories (X-axis labels)
    let categories = ['January', 'February', 'March', 'April', 'May', 'June'];

    // Observable for chart data and series
    this.chartData = ko.observableArray(chartData); // Observable array for chart data
    this.series = ko.observableArray(chartData);    // Observable array for series

    // Return the chart data
    return this.series();
};

PageModule.prototype.getSampleChartData = function () {
    // Define categories and corresponding series data
    let chartData = [
        {
            "name": "Sales",  // Series name
            "items": [100, 200, 150, 300, 250, 400]  // Values for each category
        },
        {
            "name": "Expenses",  // Another series name
            "items": [80, 180, 120, 250, 220, 350]  // Values for each category
        }
    ];

    // Define the categories (X-axis labels)
    let categories = ['January', 'February', 'March', 'April', 'May', 'June'];

    // Observable for chart data and series
    this.chartData = ko.observableArray(chartData); // Observable array for chart data
    this.series = ko.observableArray(chartData);    // Observable array for series

    // Return the chart data
    //chartData: this.chartData();
    return this.chartData();
};




  PageModule.prototype.getJSONData = function (parsedHTML) { // HTML data in the input



    // Example HTML string with escaped characters (with literal backslashes)
    let htmlString = '<table border=\\\"1\\\" class=\\\"dataframe\\\">';

    // Clean up escaped characters
    let cleanedHtmlString = parsedHTML
      .replace(/\\"/g, '"')    // Replace escaped quotes (\") with normal quotes (")
      .replace(/\\\\/g, '\\'); // Replace escaped backslashes (\\) with a single backslash (\)

    cleanedHtmlString = cleanedHtmlString
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&');



    // Now the cleaned string is ready to be inserted or used
    console.log("Cleaned up HTML: " + cleanedHtmlString);  // <table border="1" class="dataframe">


    let parser = new DOMParser();
    let doc = parser.parseFromString(cleanedHtmlString, 'text/html');

 






    // Extract table headers
    let tableHeaders = [];
    let headers = doc.querySelectorAll('table th');

    headers.forEach(header => {
      tableHeaders.push(header.innerText.trim());
    });


    let tableRows = [];
    let rows = Array.from(doc.querySelectorAll('table tbody tr'));
    rows.forEach(row => {
      let rowData = {};
      let cells = row.querySelectorAll('td');
      cells.forEach((cell, index) => {
        let cellValue = cell.innerText.trim();
        rowData[`column_${index}`] = cellValue;
      });
      if (Object.keys(rowData).length > 0) {
        tableRows.push(rowData);
      }
    });


    console.log("tableRows --------> :", tableRows);

    // Set the columns dynamically based on the headers
    let columnDefs = [];
    tableHeaders.forEach((header, index) => {
      columnDefs.push({
        headerText: header,
        field: `column_${index}`,
        sortable: 'enabled',
        resizable: 'enabled',
        width: 'auto',
        className: 'custom-column',
        sortComparer: (a, b) => {
          // Check if column is numeric (for example, "Total Amount Due" is column_1)
          if (index === 1) { // Assuming it's a numeric column (Total Amount Due is index 1)
            return a - b; // Numeric sort
          }
          return a.localeCompare(b); // Default string sort
        }
      });
    });


    console.log("columnDefs ======> " + JSON.stringify(columnDefs));

   let tableData = tableRows.map((row, index) => ({ ...row, id: `row_${index}` }));




    let dataProvider = new ArrayDataProvider(tableData, { idAttribute: 'id' });   // Create an ArrayDataProvider for pagination


    let pagingDataProvider = new PagingDataProviderView(dataProvider);     // Wrap the dataProvider in PagingDataProviderView

    // Set columns and data for the table
    let dynamicTable = document.getElementById('dynamicTable');
    dynamicTable.setProperty('columns', columnDefs);  // Columns defined earlier
    dynamicTable.setProperty('data', pagingDataProvider);  // Set the paged data

    dynamicTable.refresh();

    this.tableData = tableData;
    this.filteredData = [...tableData];

    this.setupFilterInput();

    return pagingDataProvider;


  };


  PageModule.prototype.getJSONData111 = function (parsedHTML) { // HTML data in the input



    // Example HTML string with escaped characters (with literal backslashes)
    let htmlString = '<table border=\\\"1\\\" class=\\\"dataframe\\\">';

    // Clean up escaped characters
    let cleanedHtmlString = parsedHTML
      .replace(/\\"/g, '"')    // Replace escaped quotes (\") with normal quotes (")
      .replace(/\\\\/g, '\\'); // Replace escaped backslashes (\\) with a single backslash (\)

    cleanedHtmlString = cleanedHtmlString
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&');

    console.log("Cleaned up HTML: " + cleanedHtmlString);  


    let parser = new DOMParser();
    let doc = parser.parseFromString(cleanedHtmlString, 'text/html');

    let tableHeaders = [];
    let headers = doc.querySelectorAll('table th');

    headers.forEach(header => {
      tableHeaders.push(header.innerText.trim());
    });

    let tableRows = [];
    let rows = Array.from(doc.querySelectorAll('table tbody tr'));
    rows.forEach(row => {
      let rowData = {};
      let cells = row.querySelectorAll('td');
      cells.forEach((cell, index) => {
        let cellValue = cell.innerText.trim();
        rowData[`column_${index}`] = cellValue;
      });
      if (Object.keys(rowData).length > 0) {
        tableRows.push(rowData);
      }
    });


    console.log("tableRows --------> :", tableRows);





    // Set the columns dynamically based on the headers
    let columnDefs = [];
    tableHeaders.forEach((header, index) => {
      columnDefs.push({
        headerText: header,
        field: `column_${index}`,
        sortable: 'enabled',
        resizable: 'enabled',
        width: 'auto',
        // weigth: "1",
        className: 'custom-column',
        sortComparer: (a, b) => {
          // Check if column is numeric (for example, "Total Amount Due" is column_1)
          if (index === 1) { // Assuming it's a numeric column (Total Amount Due is index 1)
            return a - b; // Numeric sort
          }
          return a.localeCompare(b); // Default string sort
        }
      });
    });


    console.log("columnDefs ======> " + JSON.stringify(columnDefs));


    /*
    let tableData = tableRows.map(row => {
      let rowObject = {};
      row.forEach((cell, index) => {
        rowObject[`column_${index}`] = cell;
      });
      return rowObject;
    }); */

    let tableData = tableRows.map(row => {
      let rowObject = {};  // Initialize rowObject

      // Iterate over the row properties (which are columns)
      Object.values(row).forEach((cell, index) => {
        rowObject[`column_${index}`] = cell; // Map cell values to rowObject
      });

      return rowObject;  // Return the populated rowObject
    });



    console.log("tableData ======> " + JSON.stringify(tableData));


    // Create a data provider
    let dynamicTable = document.getElementById('dynamicTable');
    dynamicTable.setProperty('columns', columnDefs);
    // let dataProvider = new ArrayDataProvider(tableData, { idAttribute: 'column_0' });
    // dynamicTable.setProperty('data', dataProvider);

    let dataProvider = new ArrayDataProvider(tableData.map((row, index) => (
      { ...row, id: `row_${index}` } // Add a unique `id` for each row
    )), { idAttribute: 'id' });  // Use the newly added `id` field


    dynamicTable.setProperty('data', dataProvider);
    dynamicTable.refresh();

    // pagination

    let tableDataForPagination = tableRows.map((row, index) => ({ ...row, id: `row_${index}` }));

    let dataProviderForPagination = new ArrayDataProvider(tableDataForPagination, { idAttribute: 'id' });
    let pagingDataProvider = new PagingDataProviderView(dataProviderForPagination);     // Wrap the dataProvider in PagingDataProviderView

    //console.log("dataProvider =====33=> " + JSON.stringify(dataProvider));





    this.tableData = tableData;
    this.filteredData = [...tableData];


    // Default pagination settings
    this.rowsPerPage = 10;
    this.currentPage = 1;
    this.totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);
    this.updatePageData(this.rowsPerPage);
    this.setupFilterInput();

    //return new PagingDataProviderView(new ArrayDataProvider(dataProvider, { idAttribute: 'id' }));
    //return new PagingDataProviderView(dataProvider);

    return pagingDataProvider;


  };

  // Function to setup the filter input
  PageModule.prototype.setupFilterInput = function () {
  let filterInput = document.getElementById('filterText');
  console.log("filterInput: " + filterInput);

  if (filterInput) {
    filterInput.addEventListener('keyup', (event) => {
      let filterValue = event.target.value.toLowerCase();
      filterValue = filterValue.replace(/,/g, '');  

      let filteredData;
      if (filterValue === '') {
        
        filteredData = this.tableData;
      } else {
        filteredData = this.tableData.filter(row => {
          return Object.values(row).some(cell => {
            let cellValue = String(cell).toLowerCase();  
            cellValue = cellValue.replace(/,/g, '');
            return cellValue.includes(filterValue);
          });
        });
      }


      this.filteredData = filteredData;


      let dataProvider = new ArrayDataProvider(filteredData, { idAttribute: 'id' });


      let pagingDataProvider = new PagingDataProviderView(dataProvider);


      let dynamicTable = document.getElementById('dynamicTable');
      dynamicTable.setProperty('data', pagingDataProvider);
      dynamicTable.refresh();

      let pagingControl = document.querySelector('oj-paging-control');
      if (pagingControl) {
        pagingControl.setProperty('data', pagingDataProvider);
      }
    });
  } else {
    console.log("filterInput is cleared!!!");
  }
};





  /*
    PageModule.prototype.setupFilterInput = function () {
  
      const filterValue = document.getElementById('filterText').value.toLowerCase();
      let filteredData = this.tableData.filter(row =>
        row.some(cell => cell.toString().toLowerCase().includes(filterValue))
      );
  
  
      // Update the table with filtered data
      this.filteredData = filteredData;
  
      // Create a new data provider with the filtered data
        let dataProvider = new ArrayDataProvider(this.filteredData, { idAttribute: 'column_0' });
  
        // Update the data property of the oj-table
        let dynamicTable = document.getElementById('dynamicTable');
        dynamicTable.setProperty('data', dataProvider);
  
        // Optionally refresh the table to reflect changes
        dynamicTable.refresh();
  
    };
    */



  PageModule.prototype.updatePageData = function (rowsperPage) {


    console.log("rowsperPage : ================> " + rowsperPage);


    this.rowsPerPage = rowsperPage || this.rowsPerPage;
    let start = (this.currentPage - 1) * this.rowsPerPage;
    let end = start + this.rowsPerPage;

    console.log("this.rowsPerPage : ================> " + this.rowsPerPage);

    console.log("start : ================> " + start);
    console.log("end   : ================> " + end);



    this.pageData = this.filteredData.slice(start, end);

    //console.log("pageData   : ================> " + JSON.stringify(this.pageData));


    let dataProvider = new ArrayDataProvider(this.pageData, { idAttribute: 'id' });

    let dynamicTable = document.getElementById('dynamicTable');
    dynamicTable.setProperty('data', dataProvider);


    dynamicTable.refresh();
  };


PageModule.prototype.getTableDataFromJSON = function (jsonData) { 


  console.log("getTableDataFromJSON: "+JSON.stringify(jsonData));


  let tableHeaders = Object.keys(jsonData[0]);
  

  let tableRows = jsonData.map((row, index) => {
    let rowData = {};
    tableHeaders.forEach((header, colIndex) => {
      rowData[`column_${colIndex}`] = row[header]; 
    });
    return { ...rowData, id: `row_${index}` }; 
  });


  let columnDefs = tableHeaders.map((header, index) => {
    return {
      headerText: header,
      field: `column_${index}`,
      sortable: 'enabled',
      resizable: 'enabled',
      width: 'auto',
      className: 'custom-column',
      sortComparer: (a, b) => {
        
        if (index === 1) {  
          return a - b;  
        }
        return a.localeCompare(b); 
      }
    };
  });



   let tableData = tableRows.map((row, index) => ({ ...row, id: `row_${index}` }));




    let dataProvider = new ArrayDataProvider(tableData, { idAttribute: 'id' });   // Create an ArrayDataProvider for pagination


    let pagingDataProvider = new PagingDataProviderView(dataProvider);     // Wrap the dataProvider in PagingDataProviderView

    // Set columns and data for the table
    let dynamicTable = document.getElementById('dynamicTable');
    dynamicTable.setProperty('columns', columnDefs);  // Columns defined earlier
    dynamicTable.setProperty('data', pagingDataProvider);  // Set the paged data

    dynamicTable.refresh();

    this.tableData = tableData;
    this.filteredData = [...tableData];

    this.setupFilterInput();

    return pagingDataProvider;

};


// Amount Due vs Past Due Days
  let jsonDataFull = {
    "data": [
      {
        "alignmentgroup": "True",
        "customdata": [
          [
            "2024-04-05T00:00:00"
          ],
          [
            "2024-04-04T00:00:00"
          ],
          [
            "2024-04-04T00:00:00"
          ],
          [
            "2024-04-04T00:00:00"
          ],
          [
            "2024-04-03T00:00:00"
          ],
          [
            "2024-04-03T00:00:00"
          ],
          [
            "2024-04-03T00:00:00"
          ],
          [
            "2024-04-02T00:00:00"
          ],
          [
            "2024-04-02T00:00:00"
          ],
          [
            "2024-04-01T00:00:00"
          ],
          [
            "2024-04-01T00:00:00"
          ],
          [
            "2024-03-31T00:00:00"
          ],
          [
            "2024-03-31T00:00:00"
          ],
          [
            "2024-03-28T00:00:00"
          ],
          [
            "2024-03-28T00:00:00"
          ],
          [
            "2024-03-28T00:00:00"
          ],
          [
            "2024-03-27T00:00:00"
          ],
          [
            "2024-03-27T00:00:00"
          ],
          [
            "2024-03-26T00:00:00"
          ],
          [
            "2024-03-26T00:00:00"
          ],
          [
            "2024-03-25T00:00:00"
          ],
          [
            "2024-03-25T00:00:00"
          ],
          [
            "2024-03-24T00:00:00"
          ],
          [
            "2024-03-24T00:00:00"
          ],
          [
            "2024-03-24T00:00:00"
          ],
          [
            "2024-03-22T00:00:00"
          ],
          [
            "2024-03-21T00:00:00"
          ],
          [
            "2024-03-21T00:00:00"
          ],
          [
            "2024-03-21T00:00:00"
          ],
          [
            "2024-03-21T00:00:00"
          ],
          [
            "2024-03-21T00:00:00"
          ],
          [
            "2024-03-21T00:00:00"
          ],
          [
            "2024-03-21T00:00:00"
          ],
          [
            "2024-03-14T00:00:00"
          ],
          [
            "2024-03-14T00:00:00"
          ],
          [
            "2024-03-12T00:00:00"
          ],
          [
            "2024-03-12T00:00:00"
          ],
          [
            "2024-03-11T00:00:00"
          ],
          [
            "2024-03-10T00:00:00"
          ],
          [
            "2024-03-07T00:00:00"
          ],
          [
            "2024-03-07T00:00:00"
          ],
          [
            "2024-03-04T00:00:00"
          ],
          [
            "2024-03-04T00:00:00"
          ],
          [
            "2024-02-29T00:00:00"
          ],
          [
            "2024-02-23T00:00:00"
          ],
          [
            "2024-02-16T00:00:00"
          ],
          [
            "2024-02-08T00:00:00"
          ],
          [
            "2024-02-02T00:00:00"
          ],
          [
            "2024-02-01T00:00:00"
          ],
          [
            "2024-02-01T00:00:00"
          ]
        ],
        "hovertemplate": "Invoice Number=%{x}<br>Amount Due=%{y}<br>Due Date=%{customdata[0]}<br>Past Due Days=%{marker.color}<extra></extra>",
        "legendgroup": "",
        "marker": {
          "color": [
            41,
            42,
            42,
            42,
            43,
            43,
            43,
            44,
            44,
            45,
            45,
            46,
            46,
            49,
            49,
            49,
            50,
            50,
            51,
            51,
            52,
            52,
            53,
            53,
            53,
            55,
            56,
            56,
            56,
            56,
            56,
            56,
            56,
            63,
            63,
            65,
            65,
            66,
            67,
            70,
            70,
            73,
            73,
            77,
            83,
            90,
            98,
            104,
            105,
            105
          ],
          "coloraxis": "coloraxis",
          "pattern": {
            "shape": ""
          }
        },
        "name": "",
        "offsetgroup": "",
        "orientation": "v",
        "showlegend": false,
        "textposition": "auto",
        "x": [
          "ERS-13623-229563",
          "ERS-13617-229286",
          "ERS-13555-227325",
          "ERS-13630-229762",
          "ERS-13610-229265",
          "ERS-13612-229267",
          "ERS-13604-229114",
          "ERS-13608-229243",
          "ERS-13601-229105",
          "ERS-13602-229112",
          "ERS-13601-229104",
          "UK201039706",
          "ERS-13598-229082",
          "ERS-13592-228630",
          "ERS-13596-228634",
          "ERS-13521-226257",
          "ERS-13585-228351",
          "ERS-13587-228355",
          "ERS-13585-228350",
          "ERS-13587-228354",
          "ERS-13585-228349",
          "ERS-13587-228353",
          "ERS-13583-228347",
          "UK201039699",
          "ERS-13579-228109",
          "ERS-13569-227923",
          "ERS-13571-227928",
          "ERS-13575-228081",
          "ERS-13581-228344",
          "ERS-13567-227770",
          "ERS-13574-227943",
          "ERS-13563-227570",
          "ERS-13492-225608",
          "UK201039689",
          "ERS-13526-226475",
          "ERS-13524-226473",
          "ERS-13547-227281",
          "ERS-13520-226256",
          "ERS-13515-226091",
          "UK201039682",
          "ERS-13501-225763",
          "ERS-13490-225604",
          "ERS-13490-225606",
          "ERS-13470-225164",
          "ERS-13445-224321",
          "ERS-13418-223499",
          "ERS-13393-222295",
          "ERS-13365-221806",
          "ERS-13365-221805",
          "ERS-13373-221916"
        ],
        "xaxis": "x",
        "y": [
          1103.81,
          978.82,
          25167.33,
          36425.61,
          815.69,
          815.69,
          14329.13,
          2447.06,
          22076.14,
          3099.6,
          11038.07,
          4573.11,
          14349.49,
          6362.34,
          15453.29,
          25167.33,
          326.27,
          22076.14,
          3589.01,
          39737.04,
          2936.47,
          48567.5,
          1305.1,
          4573.11,
          25387.56,
          652.55,
          1103.81,
          1103.81,
          1103.81,
          2120.78,
          2120.78,
          13956.66,
          25167.33,
          4969.08,
          13956.66,
          1468.23,
          1468.23,
          3099.6,
          652.55,
          4969.08,
          13956.66,
          2447.06,
          2447.06,
          13956.66,
          15165.74,
          15165.74,
          15165.74,
          22076.14,
          3099.6,
          3099.6
        ],
        "yaxis": "y",
        "type": "bar"
      }
    ],
    "layout": {
      "template": {
        "data": {
          "histogram2dcontour": [
            {
              "type": "histogram2dcontour",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "choropleth": [
            {
              "type": "choropleth",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              }
            }
          ],
          "histogram2d": [
            {
              "type": "histogram2d",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "heatmap": [
            {
              "type": "heatmap",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "heatmapgl": [
            {
              "type": "heatmapgl",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "contourcarpet": [
            {
              "type": "contourcarpet",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              }
            }
          ],
          "contour": [
            {
              "type": "contour",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "surface": [
            {
              "type": "surface",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "mesh3d": [
            {
              "type": "mesh3d",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              }
            }
          ],
          "scatter": [
            {
              "fillpattern": {
                "fillmode": "overlay",
                "size": 10,
                "solidity": 0.2
              },
              "type": "scatter"
            }
          ],
          "parcoords": [
            {
              "type": "parcoords",
              "line": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatterpolargl": [
            {
              "type": "scatterpolargl",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "bar": [
            {
              "error_x": {
                "color": "#2a3f5f"
              },
              "error_y": {
                "color": "#2a3f5f"
              },
              "marker": {
                "line": {
                  "color": "#E5ECF6",
                  "width": 0.5
                },
                "pattern": {
                  "fillmode": "overlay",
                  "size": 10,
                  "solidity": 0.2
                }
              },
              "type": "bar"
            }
          ],
          "scattergeo": [
            {
              "type": "scattergeo",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatterpolar": [
            {
              "type": "scatterpolar",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "histogram": [
            {
              "marker": {
                "pattern": {
                  "fillmode": "overlay",
                  "size": 10,
                  "solidity": 0.2
                }
              },
              "type": "histogram"
            }
          ],
          "scattergl": [
            {
              "type": "scattergl",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatter3d": [
            {
              "type": "scatter3d",
              "line": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              },
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scattermapbox": [
            {
              "type": "scattermapbox",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatterternary": [
            {
              "type": "scatterternary",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scattercarpet": [
            {
              "type": "scattercarpet",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "carpet": [
            {
              "aaxis": {
                "endlinecolor": "#2a3f5f",
                "gridcolor": "white",
                "linecolor": "white",
                "minorgridcolor": "white",
                "startlinecolor": "#2a3f5f"
              },
              "baxis": {
                "endlinecolor": "#2a3f5f",
                "gridcolor": "white",
                "linecolor": "white",
                "minorgridcolor": "white",
                "startlinecolor": "#2a3f5f"
              },
              "type": "carpet"
            }
          ],
          "table": [
            {
              "cells": {
                "fill": {
                  "color": "#EBF0F8"
                },
                "line": {
                  "color": "white"
                }
              },
              "header": {
                "fill": {
                  "color": "#C8D4E3"
                },
                "line": {
                  "color": "white"
                }
              },
              "type": "table"
            }
          ],
          "barpolar": [
            {
              "marker": {
                "line": {
                  "color": "#E5ECF6",
                  "width": 0.5
                },
                "pattern": {
                  "fillmode": "overlay",
                  "size": 10,
                  "solidity": 0.2
                }
              },
              "type": "barpolar"
            }
          ],
          "pie": [
            {
              "automargin": true,
              "type": "pie"
            }
          ]
        },
        "layout": {
          "autotypenumbers": "strict",
          "colorway": [
            "#636efa",
            "#EF553B",
            "#00cc96",
            "#ab63fa",
            "#FFA15A",
            "#19d3f3",
            "#FF6692",
            "#B6E880",
            "#FF97FF",
            "#FECB52"
          ],
          "font": {
            "color": "#2a3f5f"
          },
          "hovermode": "closest",
          "hoverlabel": {
            "align": "left"
          },
          "paper_bgcolor": "white",
          "plot_bgcolor": "#E5ECF6",
          "polar": {
            "bgcolor": "#E5ECF6",
            "angularaxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            },
            "radialaxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            }
          },
          "ternary": {
            "bgcolor": "#E5ECF6",
            "aaxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            },
            "baxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            },
            "caxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            }
          },
          "coloraxis": {
            "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
            }
          },
          "colorscale": {
            "sequential": [
              [
                0,
                "#0d0887"
              ],
              [
                0.1111111111111111,
                "#46039f"
              ],
              [
                0.2222222222222222,
                "#7201a8"
              ],
              [
                0.3333333333333333,
                "#9c179e"
              ],
              [
                0.4444444444444444,
                "#bd3786"
              ],
              [
                0.5555555555555556,
                "#d8576b"
              ],
              [
                0.6666666666666666,
                "#ed7953"
              ],
              [
                0.7777777777777778,
                "#fb9f3a"
              ],
              [
                0.8888888888888888,
                "#fdca26"
              ],
              [
                1,
                "#f0f921"
              ]
            ],
            "sequentialminus": [
              [
                0,
                "#0d0887"
              ],
              [
                0.1111111111111111,
                "#46039f"
              ],
              [
                0.2222222222222222,
                "#7201a8"
              ],
              [
                0.3333333333333333,
                "#9c179e"
              ],
              [
                0.4444444444444444,
                "#bd3786"
              ],
              [
                0.5555555555555556,
                "#d8576b"
              ],
              [
                0.6666666666666666,
                "#ed7953"
              ],
              [
                0.7777777777777778,
                "#fb9f3a"
              ],
              [
                0.8888888888888888,
                "#fdca26"
              ],
              [
                1,
                "#f0f921"
              ]
            ],
            "diverging": [
              [
                0,
                "#8e0152"
              ],
              [
                0.1,
                "#c51b7d"
              ],
              [
                0.2,
                "#de77ae"
              ],
              [
                0.3,
                "#f1b6da"
              ],
              [
                0.4,
                "#fde0ef"
              ],
              [
                0.5,
                "#f7f7f7"
              ],
              [
                0.6,
                "#e6f5d0"
              ],
              [
                0.7,
                "#b8e186"
              ],
              [
                0.8,
                "#7fbc41"
              ],
              [
                0.9,
                "#4d9221"
              ],
              [
                1,
                "#276419"
              ]
            ]
          },
          "xaxis": {
            "gridcolor": "white",
            "linecolor": "white",
            "ticks": "",
            "title": {
              "standoff": 15
            },
            "zerolinecolor": "white",
            "automargin": true,
            "zerolinewidth": 2
          },
          "yaxis": {
            "gridcolor": "white",
            "linecolor": "white",
            "ticks": "",
            "title": {
              "standoff": 15
            },
            "zerolinecolor": "white",
            "automargin": true,
            "zerolinewidth": 2
          },
          "scene": {
            "xaxis": {
              "backgroundcolor": "#E5ECF6",
              "gridcolor": "white",
              "linecolor": "white",
              "showbackground": true,
              "ticks": "",
              "zerolinecolor": "white",
              "gridwidth": 2
            },
            "yaxis": {
              "backgroundcolor": "#E5ECF6",
              "gridcolor": "white",
              "linecolor": "white",
              "showbackground": true,
              "ticks": "",
              "zerolinecolor": "white",
              "gridwidth": 2
            },
            "zaxis": {
              "backgroundcolor": "#E5ECF6",
              "gridcolor": "white",
              "linecolor": "white",
              "showbackground": true,
              "ticks": "",
              "zerolinecolor": "white",
              "gridwidth": 2
            }
          },
          "shapedefaults": {
            "line": {
              "color": "#2a3f5f"
            }
          },
          "annotationdefaults": {
            "arrowcolor": "#2a3f5f",
            "arrowhead": 0,
            "arrowwidth": 1
          },
          "geo": {
            "bgcolor": "white",
            "landcolor": "#E5ECF6",
            "subunitcolor": "white",
            "showland": true,
            "showlakes": true,
            "lakecolor": "white"
          },
          "title": {
            "x": 0.05
          },
          "mapbox": {
            "style": "light"
          }
        }
      },
      "xaxis": {
        "anchor": "y",
        "domain": [
          0,
          1
        ],
        "title": {
          "text": "Invoice Number"
        }
      },
      "yaxis": {
        "anchor": "x",
        "domain": [
          0,
          1
        ],
        "title": {
          "text": "Amount Due"
        }
      },
      "coloraxis": {
        "colorbar": {
          "title": {
            "text": "Past Due Days"
          }
        },
        "colorscale": [
          [
            0,
            "rgb(247,251,255)"
          ],
          [
            0.125,
            "rgb(222,235,247)"
          ],
          [
            0.25,
            "rgb(198,219,239)"
          ],
          [
            0.375,
            "rgb(158,202,225)"
          ],
          [
            0.5,
            "rgb(107,174,214)"
          ],
          [
            0.625,
            "rgb(66,146,198)"
          ],
          [
            0.75,
            "rgb(33,113,181)"
          ],
          [
            0.875,
            "rgb(8,81,156)"
          ],
          [
            1,
            "rgb(8,48,107)"
          ]
        ]
      },
      "legend": {
        "tracegroupgap": 0
      },
      "margin": {
        "t": 60
      },
      "barmode": "relative",
      "title": {
        "text": "Amount Due vs Past Due Days"
      }
    }
  };

  // Invoice Type
  let jsonDataFull2 = {
    "data": [
      {
        "hovertemplate": "Invoice Type=%{x}<br>Invoice Type Id=%{y}<extra></extra>",
        "legendgroup": "",
        "line": {
          "color": "#636efa",
          "dash": "solid"
        },
        "marker": {
          "symbol": "circle"
        },
        "mode": "lines",
        "name": "",
        "orientation": "v",
        "showlegend": false,
        "x": [
          "CREDIT",
          "RETAINAGE RELEASE",
          "STANDARD",
          "EXPENSE REPORT"
        ],
        "xaxis": "x",
        "y": [
          1,
          2,
          3,
          4
        ],
        "yaxis": "y",
        "type": "scatter"
      }
    ],
    "layout": {
      "template": {
        "data": {
          "histogram2dcontour": [
            {
              "type": "histogram2dcontour",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "choropleth": [
            {
              "type": "choropleth",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              }
            }
          ],
          "histogram2d": [
            {
              "type": "histogram2d",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "heatmap": [
            {
              "type": "heatmap",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "heatmapgl": [
            {
              "type": "heatmapgl",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "contourcarpet": [
            {
              "type": "contourcarpet",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              }
            }
          ],
          "contour": [
            {
              "type": "contour",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "surface": [
            {
              "type": "surface",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              },
              "colorscale": [
                [
                  0,
                  "#0d0887"
                ],
                [
                  0.1111111111111111,
                  "#46039f"
                ],
                [
                  0.2222222222222222,
                  "#7201a8"
                ],
                [
                  0.3333333333333333,
                  "#9c179e"
                ],
                [
                  0.4444444444444444,
                  "#bd3786"
                ],
                [
                  0.5555555555555556,
                  "#d8576b"
                ],
                [
                  0.6666666666666666,
                  "#ed7953"
                ],
                [
                  0.7777777777777778,
                  "#fb9f3a"
                ],
                [
                  0.8888888888888888,
                  "#fdca26"
                ],
                [
                  1,
                  "#f0f921"
                ]
              ]
            }
          ],
          "mesh3d": [
            {
              "type": "mesh3d",
              "colorbar": {
                "outlinewidth": 0,
                "ticks": ""
              }
            }
          ],
          "scatter": [
            {
              "fillpattern": {
                "fillmode": "overlay",
                "size": 10,
                "solidity": 0.2
              },
              "type": "scatter"
            }
          ],
          "parcoords": [
            {
              "type": "parcoords",
              "line": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatterpolargl": [
            {
              "type": "scatterpolargl",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "bar": [
            {
              "error_x": {
                "color": "#2a3f5f"
              },
              "error_y": {
                "color": "#2a3f5f"
              },
              "marker": {
                "line": {
                  "color": "#E5ECF6",
                  "width": 0.5
                },
                "pattern": {
                  "fillmode": "overlay",
                  "size": 10,
                  "solidity": 0.2
                }
              },
              "type": "bar"
            }
          ],
          "scattergeo": [
            {
              "type": "scattergeo",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatterpolar": [
            {
              "type": "scatterpolar",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "histogram": [
            {
              "marker": {
                "pattern": {
                  "fillmode": "overlay",
                  "size": 10,
                  "solidity": 0.2
                }
              },
              "type": "histogram"
            }
          ],
          "scattergl": [
            {
              "type": "scattergl",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatter3d": [
            {
              "type": "scatter3d",
              "line": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              },
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scattermapbox": [
            {
              "type": "scattermapbox",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scatterternary": [
            {
              "type": "scatterternary",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "scattercarpet": [
            {
              "type": "scattercarpet",
              "marker": {
                "colorbar": {
                  "outlinewidth": 0,
                  "ticks": ""
                }
              }
            }
          ],
          "carpet": [
            {
              "aaxis": {
                "endlinecolor": "#2a3f5f",
                "gridcolor": "white",
                "linecolor": "white",
                "minorgridcolor": "white",
                "startlinecolor": "#2a3f5f"
              },
              "baxis": {
                "endlinecolor": "#2a3f5f",
                "gridcolor": "white",
                "linecolor": "white",
                "minorgridcolor": "white",
                "startlinecolor": "#2a3f5f"
              },
              "type": "carpet"
            }
          ],
          "table": [
            {
              "cells": {
                "fill": {
                  "color": "#EBF0F8"
                },
                "line": {
                  "color": "white"
                }
              },
              "header": {
                "fill": {
                  "color": "#C8D4E3"
                },
                "line": {
                  "color": "white"
                }
              },
              "type": "table"
            }
          ],
          "barpolar": [
            {
              "marker": {
                "line": {
                  "color": "#E5ECF6",
                  "width": 0.5
                },
                "pattern": {
                  "fillmode": "overlay",
                  "size": 10,
                  "solidity": 0.2
                }
              },
              "type": "barpolar"
            }
          ],
          "pie": [
            {
              "automargin": true,
              "type": "pie"
            }
          ]
        },
        "layout": {
          "autotypenumbers": "strict",
          "colorway": [
            "#636efa",
            "#EF553B",
            "#00cc96",
            "#ab63fa",
            "#FFA15A",
            "#19d3f3",
            "#FF6692",
            "#B6E880",
            "#FF97FF",
            "#FECB52"
          ],
          "font": {
            "color": "#2a3f5f"
          },
          "hovermode": "closest",
          "hoverlabel": {
            "align": "left"
          },
          "paper_bgcolor": "white",
          "plot_bgcolor": "#E5ECF6",
          "polar": {
            "bgcolor": "#E5ECF6",
            "angularaxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            },
            "radialaxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            }
          },
          "ternary": {
            "bgcolor": "#E5ECF6",
            "aaxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            },
            "baxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            },
            "caxis": {
              "gridcolor": "white",
              "linecolor": "white",
              "ticks": ""
            }
          },
          "coloraxis": {
            "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
            }
          },
          "colorscale": {
            "sequential": [
              [
                0,
                "#0d0887"
              ],
              [
                0.1111111111111111,
                "#46039f"
              ],
              [
                0.2222222222222222,
                "#7201a8"
              ],
              [
                0.3333333333333333,
                "#9c179e"
              ],
              [
                0.4444444444444444,
                "#bd3786"
              ],
              [
                0.5555555555555556,
                "#d8576b"
              ],
              [
                0.6666666666666666,
                "#ed7953"
              ],
              [
                0.7777777777777778,
                "#fb9f3a"
              ],
              [
                0.8888888888888888,
                "#fdca26"
              ],
              [
                1,
                "#f0f921"
              ]
            ],
            "sequentialminus": [
              [
                0,
                "#0d0887"
              ],
              [
                0.1111111111111111,
                "#46039f"
              ],
              [
                0.2222222222222222,
                "#7201a8"
              ],
              [
                0.3333333333333333,
                "#9c179e"
              ],
              [
                0.4444444444444444,
                "#bd3786"
              ],
              [
                0.5555555555555556,
                "#d8576b"
              ],
              [
                0.6666666666666666,
                "#ed7953"
              ],
              [
                0.7777777777777778,
                "#fb9f3a"
              ],
              [
                0.8888888888888888,
                "#fdca26"
              ],
              [
                1,
                "#f0f921"
              ]
            ],
            "diverging": [
              [
                0,
                "#8e0152"
              ],
              [
                0.1,
                "#c51b7d"
              ],
              [
                0.2,
                "#de77ae"
              ],
              [
                0.3,
                "#f1b6da"
              ],
              [
                0.4,
                "#fde0ef"
              ],
              [
                0.5,
                "#f7f7f7"
              ],
              [
                0.6,
                "#e6f5d0"
              ],
              [
                0.7,
                "#b8e186"
              ],
              [
                0.8,
                "#7fbc41"
              ],
              [
                0.9,
                "#4d9221"
              ],
              [
                1,
                "#276419"
              ]
            ]
          },
          "xaxis": {
            "gridcolor": "white",
            "linecolor": "white",
            "ticks": "",
            "title": {
              "standoff": 15
            },
            "zerolinecolor": "white",
            "automargin": true,
            "zerolinewidth": 2
          },
          "yaxis": {
            "gridcolor": "white",
            "linecolor": "white",
            "ticks": "",
            "title": {
              "standoff": 15
            },
            "zerolinecolor": "white",
            "automargin": true,
            "zerolinewidth": 2
          },
          "scene": {
            "xaxis": {
              "backgroundcolor": "#E5ECF6",
              "gridcolor": "white",
              "linecolor": "white",
              "showbackground": true,
              "ticks": "",
              "zerolinecolor": "white",
              "gridwidth": 2
            },
            "yaxis": {
              "backgroundcolor": "#E5ECF6",
              "gridcolor": "white",
              "linecolor": "white",
              "showbackground": true,
              "ticks": "",
              "zerolinecolor": "white",
              "gridwidth": 2
            },
            "zaxis": {
              "backgroundcolor": "#E5ECF6",
              "gridcolor": "white",
              "linecolor": "white",
              "showbackground": true,
              "ticks": "",
              "zerolinecolor": "white",
              "gridwidth": 2
            }
          },
          "shapedefaults": {
            "line": {
              "color": "#2a3f5f"
            }
          },
          "annotationdefaults": {
            "arrowcolor": "#2a3f5f",
            "arrowhead": 0,
            "arrowwidth": 1
          },
          "geo": {
            "bgcolor": "white",
            "landcolor": "#E5ECF6",
            "subunitcolor": "white",
            "showland": true,
            "showlakes": true,
            "lakecolor": "white"
          },
          "title": {
            "x": 0.05
          },
          "mapbox": {
            "style": "light"
          }
        }
      },
      "xaxis": {
        "anchor": "y",
        "domain": [
          0,
          1
        ],
        "title": {
          "text": "Invoice Type"
        }
      },
      "yaxis": {
        "anchor": "x",
        "domain": [
          0,
          1
        ],
        "title": {
          "text": "Invoice Type Id"
        }
      },
      "legend": {
        "tracegroupgap": 0
      },
      "margin": {
        "t": 60
      }
    }
  };

  // Updated function to fetch the values from the actual data
  PageModule.prototype.getBarChartData = function () {

    // Extract labels and data from the input (rest service response)

    let jsonDataBar = jsonDataFull; // Amount Due vs Past Due Days
    //let jsonDataBar = jsonDataFull2; // Invoice Type vs Invoice Type IDs

    const hovertemplate = jsonDataBar.data[0].hovertemplate;
    const xAxisLabel = hovertemplate.substring(0, hovertemplate.indexOf('=%{x}'));
    const xLabel = xAxisLabel.replace(/ /g, '');

    const yAxisLabel = hovertemplate.substring(0, hovertemplate.indexOf('=%{y}')).split('=%{x}<br>')[1];
    const yLabel = yAxisLabel.replace(/ /g, ''); // remove spaces

    const titleText = jsonDataBar.layout?.title?.text;

    console.log("titleText", titleText);
    console.log("X Label:", xLabel);
    console.log("Y Label:", yLabel);


    // "hovertemplate": "Invoice Number=%{x}<br>Amount Due=%{y}<br>Due Date=%{customdata[0]}<br>Past Due Days=%{marker.color}<extra></extra>",
    //  "hovertemplate": "Invoice Type=%{x}<br>Invoice Type Id=%{y}<extra></extra>",
    const additionalFields = [];
    const regex = /<br>(.*?)=%{.*?}/g;
    let match;
    while ((match = regex.exec(hovertemplate))) {
      const fieldName = match[1].replace(/ /g, '');
      additionalFields.push(fieldName);
    }

    console.log("Additional Fields:", additionalFields);




    const mynewArr = [];
    //  [yLabel]: jsonDataBar.data[0].y[key],
    // Object.entries(jsonDataBar.data[0].x).forEach(([key, value]) => {
    //   mynewArr.push({

    //     "series": jsonDataBar.data[0].marker?.color?.[key] || "Group A",
    //     "group": jsonDataBar.data[0].y[key],
    //     "value": value
    //   });
    // });

    Object.entries(jsonDataBar.data[0].x).forEach(([key, value]) => {
      mynewArr.push({
        "value": jsonDataBar.data[0].y[key], // y-axis
        "group": value, // x-axis
        "series": jsonDataBar.data[0].marker?.color?.[key] || "Group A" // series or group by parameter
      });


    });


    console.log("mynewArr: " + JSON.stringify(mynewArr));

    let showLegend = mynewArr.some(item => item.series !== "Group A");




    const tooltipRenderer = function (xLabel1, yLabel1) {
      return function (context) {
        const data = context.data;

        return `
      <div>
        <strong>Series:</strong> ${data.series}<br>
        <strong>${xLabel1}:</strong> ${data.group}<br>
        <strong>${yLabel1}:</strong> ${data.value}
      </div>
    `;
      };
    };




    console.log("tooltipRenderer: " + tooltipRenderer);

    return {
      usageGraphData: mynewArr,
      xAxisLabel: xAxisLabel,
      yAxisLabel: yAxisLabel,
      titleText: titleText,
      showLegend: showLegend,
      tooltipRenderer: tooltipRenderer
    };

  };





  return PageModule;
});
