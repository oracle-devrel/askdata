define([], () => {
  'use strict';

  class AppModule {
  }

   AppModule.prototype.getDetailedInsightsSessionVar = function () {

      console.log("getDetailedInsights: "+sessionStorage.getItem("getDetailedInsights"));
      return sessionStorage.getItem("getDetailedInsights");

    };
  
  return AppModule;
});
