define(['ojs/ojcore', 'ojs/ojtable', 'ojs/ojarraydataprovider', 'ojs/ojpagingdataproviderview', 'knockout', 'ojs/ojcontext'], (ojcore, ojtable, ArrayDataProvider, PagingDataProviderView, ko, ojcontext) => {
  'use strict';
  var PageModule = function PageModule(context) { }
  const queryParams = {};

  PageModule.prototype.extractQueryParams = function () {
    var queryString = window.location.search;
    queryString = queryString.slice(queryString.indexOf('?') + 1);
    const pairs = queryString.split('&');
    for (var i = 0; i < pairs.length; i++) {
      const [key, value] = pairs[i].split('=');
      queryParams[key] = decodeURIComponent(value);
    };
  };

  PageModule.prototype.lookupQueryParam = function (name) {
    return queryParams[name];
  };

  PageModule.prototype.getTableDataFromJSON = function (jsonData) {
    let dynamicTable = document.getElementById('dynamicTable');
    
    const emptyDataProvider = new ArrayDataProvider([], { idAttribute: 'id' });
    const emptyPagingProvider = new PagingDataProviderView(emptyDataProvider);
    if (!jsonData || jsonData.length === 0) {
      // Clear columns and set empty data provider
      if (dynamicTable) {
        dynamicTable.setProperty('columns', []);
        dynamicTable.setProperty('data', emptyPagingProvider);
        dynamicTable.refresh();
      }
      this.tableData = [];
      this.setupFilterInput();
      return emptyPagingProvider;
    }
    
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
    dynamicTable.setProperty('columns', columnDefs);  // Columns defined earlier
    dynamicTable.setProperty('data', pagingDataProvider);  // Set the paged data
    dynamicTable.refresh();
    this.tableData = tableData;
    this.setupFilterInput();
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

  PageModule.prototype.createChartDataProvider = function (chartData) {
    return new ArrayDataProvider(chartData, {
      keyAttributes: 'id',
      dataTypes: {
        id: 'number',
        series: 'string',
        group: 'string',
        value: 'number',
        x: 'number',
        y: 'number',
        z: 'number'
      }
    });
  };

  PageModule.prototype.transformChartData = function (rawData, chartType) {
    const isPieOrFunnel = chartType === 'pie' || chartType === 'funnel';
    const chartData = rawData.flatMap((series, seriesIndex) =>
      (series.data || []).map((item, itemIndex) => {
        // For pie and funnel charts, swap series and group
        if (isPieOrFunnel) {
          return {
            id: seriesIndex * 1000 + itemIndex,
            series: item.group, // Swap: Use group as series for pie/funnel
            group: series.series, // Swap: Use series as group for pie/funnel
            value: item.value,
            x: item.x,
            y: item.y,
            z: item.z
          };
        } else {
          // Normal mapping for other chart types
          return {
            id: seriesIndex * 1000 + itemIndex,
            series: series.series,
            group: item.group,
            value: item.value,
            x: item.x,
            y: item.y,
            z: item.z
          };
        }
      })
    );
    return chartData;
  };

  PageModule.prototype.stopEvent = function(context) {
  if (context && context.originalEvent) {
    context.originalEvent.stopPropagation();
  }
  return true;
};


  return PageModule;
});
