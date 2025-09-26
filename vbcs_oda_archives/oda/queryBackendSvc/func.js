/***
 
  This function handles an invocation that sets the "Oracle-Bots-Fn-Path" header to determine which component to invoke or if metadata should be returned.
 
***/
 
const fdk = require('@fnproject/fdk');
const OracleBotLib = require('@oracle/bots-node-sdk/lib');
const path = require("path");
 
const BOTS_FN_PATH_HEADER = "Oracle-Bots-Fn-Path";
const METADATA_PATH = "metadata";
const COMPONENT_PREFIX = "components/";
 
let shell;
let componentsRegistry;
 
const getComponentsRegistry = function (packagePath) {
    let registry = require(packagePath);
    if (registry.components) {
        return OracleBotLib.ComponentRegistry.create(registry.components, path.join(process.cwd(), packagePath));
    }
    return null;
}
 
componentsRegistry = getComponentsRegistry('.');
if (componentsRegistry && componentsRegistry.getComponents().size > 0) {
    shell = OracleBotLib.ComponentShell({logger: console}, componentsRegistry);
    if (!shell) {
        throw new Error("Failed to initialize Bots Node SDK");
    }
} else {
    throw new Error("Unable to process component registry because no components were found in package: " + packagePath);
}
 
const _handle = function (input, ctx) {
    let botsFnPath = ctx.getHeader(BOTS_FN_PATH_HEADER);
    if (!botsFnPath) {
        throw new Error("Missing required header " +  BOTS_FN_PATH_HEADER);
    } else if (botsFnPath === METADATA_PATH) {
        return shell.getAllComponentMetadata();
    } else if (botsFnPath.startsWith(COMPONENT_PREFIX)) {
        let componentName = botsFnPath.substring(COMPONENT_PREFIX.length);
        if (!componentName) {
            throw new Error("The component name is missing from the header " + BOTS_FN_PATH_HEADER + ": " + botsFnPath);
        }
        return new Promise((resolve) => {
            let callback = (err, data) => {
                if (!err) {
                    resolve(data);
                } else {
                    console.log("Component invocation failed", err.stack);
                    throw err;
                }
            };
            shell.invokeComponentByName(componentName, input, {logger: () => console}, callback);
            });
    }
};
 
fdk.handle(function (input, ctx) {
    try {
        return _handle(input, ctx);
    } catch (err) {
        console.log("Function failed", err.stack);
        throw err;
    }
});