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