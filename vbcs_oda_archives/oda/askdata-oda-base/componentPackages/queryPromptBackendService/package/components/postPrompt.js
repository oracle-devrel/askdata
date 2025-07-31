'use strict';

// Documentation for writing custom components: https://github.com/oracle/bots-node-sdk/blob/master/CUSTOM_COMPONENT.md

// You can use your favorite http client package to make REST calls, however, the node fetch API is pre-installed with the bots-node-sdk.
// Documentation can be found at https://www.npmjs.com/package/node-fetch
// Un-comment the next line if you want to make REST calls using node-fetch. 
 const fetch = require("node-fetch");
 
module.exports = {
  metadata: () => ({
    name: 'askdata.postPrompt',
    properties: {
      question: { required: true, type: 'string' },
	  sessionId: { required: true, type: 'string' },
	  userName: { required: false, type: 'string' },
	  domain: { required: false, type: 'string' },
	  groupName: { required: false, type: 'string' },
	  url: { required: true, type: 'string' },
	  token: { required: false, type: 'string' },
	  variable: { required: false, type: 'string' }
    },
    supportedActions: ['success', 'failure']
  }),


  /**
   * invoke method gets called when the custom component state is executed in the dialog flow
   * @param {CustomComponentContext} context 
   */
  invoke: async (context, done) => {
    // Retrieve the value of component property.
    const { question } = context.properties();
    const { sessionId } = context.properties();
    const { userName } = context.properties();
    const { domain } = context.properties();
    const { groupName } = context.properties();
	const { url } = context.properties();
	const { token } = context.properties();
	const { variable } = context.properties()
	
	context.logger().info("Input parameter values: question: "+question+", sessionId: "+sessionId+", userName: "+userName+", domain: "+domain+", groupName: "+groupName);
	
	context.logger().info("Input url values: url: "+url);
	//Comment out the following line in PRODUCTION
	context.logger().info("Input token values: token: "+token);

	let payload = {
		question: question, 
		sessionid: sessionId,
		userName: userName,
		domain: domain,
		groupName: groupName		
	};
	

	try {
		const response = await fetch(url, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json',
			           'Authorization': 'Bearer '+token},
			body: JSON.stringify(payload)
		});
	    //context.logger().info("response: " + response.toString())
		const responseData = await response.json();
		context.logger().info("responseData: " + responseData.toString())
		context.logger().info("status: " + response.status)

		if (response.status === 200) {  
		    context.setVariable(variable, responseData)
			context.transition('success')
			context.keepTurn(true)
		} else {
			context.transition('failure')
			context.logger().warn(`Error: ${error.message}`)
			context.keepTurn(true)
		}
		done()
	} catch (error) {
		context.transition('failure')
		context.logger().warn(`Error: ${error.message}`)
		context.keepTurn(true)
		done()
	}
  }
};
