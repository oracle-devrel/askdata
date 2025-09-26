# AskData - Trusted AI

## Prerequisites 

This page assumes the following resources are configured:

- [Trust VM](../deployment/trust-service.c.md)
- [Trust API Gateway Deployment](../deployment/trust-api-gateway.md)

## Import APEX application

### Step 1. Select Import
![](./apex/media/image1.png)

### Step 2: Download the latest APEX app

[APEX App](../../../sql/apex/AskData_Trust_v3.2.sql)

### Step 2.1 Upload this latest export file here and click Next.

![](./apex/media/image2.png)

### Step 3: Verify all the details and click Install Application.

![](./apex/media/image3.png)

### Step 4: Click Next

![](./apex/media/image4.png)

### Step 5: Click Install Supporting Objects

![](./apex/media/image5.png)


### Step 6: Click Edit Application after succesfull installation.

![](./apex/media/image6.png)

> **NOTE** If supporting objects fails to install, that's because the idcs server still needs to be configured. This error can be ignored. Proceed to edit the application. 

## Configure APEX application:

### Step 1: Click Edit Application Definition from the application home page.

![](./apex/media/image7.png)


### Step 2: Update value of REST_API property to the proper endpoint and click Apply Changes.
The REST API is the URL for the trust API gateway.

![](./apex/media/update-rest.png)

**NOTE** Make sure to NOT include a trailing "/" at the end of your REST endpoint. 

### Step 3: IDCS SSO Integration

If the application needs IDCS SSO integration, then follow next steps. Otherwise proceed to run application.

#### Step 3.1 : Click Shared Components from application home page.

![](./apex/media/image9.png)

#### Step 3.2: Click on Authentication Schemes under Security section.

![](./apex/media/image10.png)


#### Step 3.3: Click on IAM Auth Scheme.

![](./apex/media/image11.png)


#### Step 3.4: Configure IDCS and APEX

Follow the below link to configure IDCS + APEX integration and
update the values on both sides accordingly. Then click on Make Current Scheme.

<https://docs.oracle.com/en/learn/apex-identitydomains-sso/index.html#introduction>

![](./apex/media/config-idcs.png)

**Note** In addition to the IDCS configuration above, make sure to enable "Client Credentials" and Allowed operations "Inspect". This will be used to authenticate APEX to the API Gateway with the trust APIs. 

#### Step 3.5: Update Web Credentials 

1. In APEX, select App Builder > Workspace Utilities > Web Credentials

2. Select IAM Web Cred

3. Enter your IDCS client id & secret, and make sure scope is urn:opc:idm:__myscopes__ 

> **Note** If using custom scope, use that scope instead. 

## Run APEX application:

### Step 1: Click on run button.

![](./apex/media/image13.png)

### Step 2: The home page looks like below after login.

![](./apex/media/image14.png)


### Step 3: Verify Live Certify page to check whether the REST endpoint is functioning as expected.

![](./apex/media/image15.png)

### Troubleshooting 

If your application is not displaying, double check the following 

- Web Credentials for IDCS app added to workspace utilities
- REST Endpoint is configured without trailing "/" 
- IDCS Application configured in Application definition
- Under Shared Components > Authentication Schemes 
    - Discovery URL set correctly 
    - Logout URL set correctly 
- Trust API working 

If the APEX app stops working/lags after uploading a sample prompt file, try refreshing the cache/browser; the session likely expired. If it still occurs try restarting the trust server. 
See [Trust Deployment](../deployment/trust-service.c.md#11-setup-the-nl2sql-service)

**NOTE** APEX does not support calling external APIs with self-signed certificates. If your Trust LB is using a self-signed cert, the APEX app will fail. For now we are using the API Gateway to get around this. This will fail with redirect errors when invoking the API Gateway/load balancer endpoint from APEX.

## [Return home](../../../README.md)