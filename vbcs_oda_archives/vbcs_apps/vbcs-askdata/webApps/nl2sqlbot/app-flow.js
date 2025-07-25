define([], () => {
  'use strict';

  class AppModule {
  }

  AppModule.prototype.isAuthorized = function (idcsGroupName = '', idcsRoles = {}, appProfile) {
    let userIsAuthorized = false;
    console.log("idcsGroupName: " + JSON.stringify(idcsGroupName));
    console.log("idcsRoles: " + JSON.stringify(idcsRoles));
    console.log("appProfile: " + JSON.stringify(appProfile));

    const allowedRoles = [
        "askdata_nl2sql_admin",
        "askdata_nl2sql_grp_dev",
        "askdata_nl2sql_user_grp1",
        "askdata_nl2sql_user_grp2"
    ];

    if (Array.isArray(idcsRoles)) {  
        userIsAuthorized = idcsRoles.some(role => allowedRoles.includes(role));
    } else {
        console.log("isAuthorized error: idcsRoles is not an array.");
    }

    console.log("userIsAuthorized: " + userIsAuthorized);
    return userIsAuthorized;
};



  return AppModule;
});
