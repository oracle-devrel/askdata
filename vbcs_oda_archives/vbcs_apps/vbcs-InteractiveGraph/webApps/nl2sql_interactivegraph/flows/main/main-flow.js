/**  Copyright (c) 2021, 2025 Oracle and/or its affiliates.
* Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
*/

define([], function() {
    'use strict';

    var FlowModule = function FlowModule() {};

    /**
     *
     * @param {String} arg1
     * @return {String}
     */
    FlowModule.prototype.submitFeedbackToDA = function(postbackURL, dataToSubmit) {


        var cbDataVal = JSON.stringify({
            feedbackReason: dataToSubmit
        });

        var settings = {
            "async": true,

            "crossDomain": true,
            "url": postbackURL,
            "method": "POST",
            "headers": {
                "accept": "application/json"
            },
            "processData": false,
            "data": cbDataVal
        };



        $.ajax(settings).done(function(response) {
            console.log(response);
        });
    };

    return FlowModule;
});