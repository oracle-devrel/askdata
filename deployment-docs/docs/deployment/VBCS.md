# VBCS Deployment

### Prerequisites 

This section assumes the following resources are configured: 
* [IDCS Application](./business_idcs.md)
* [Engine Application](./nl2sql_engine.md)
* [API Gateway](./business_api_gateway.md)
* [ODA](./oda.md)

### Setup Identity Group

#### Create Group

1.  Sign in to your Oracle Cloud account as an administrator.
2.  In Oracle Cloud Infrastructure Console, navigate to **Identity &
    Security**, and click **Domains**.
3.  Select \<Domain\>
4.  Click the name of the identity domain, and click **User management**.

5.  Create the following groups \[Do not change the names, as they are being referred with the same name within VBCS application\]

6.  Click Create group

<br>

![ ](./business_media/media/image16.png)

<br>

![ ](./business_media/media/image17.png)

## VBCS

### VBCS Setup – Provision VBCS Instance

#### Provision VBCS Instance

1. Open the OCI Console.

2. In the upper-left corner, click **Navigation Menu**

![ ](./business_media/media/image68.png)

3. Select **Developer Services** and then select **Visual Builder**.

<br>

![Description of admin-console-visualbuilder.png follows](./business_media/media/image69.png)

4. On the Visual Builder Instances page, from the **Compartment** drop-down list, select \<compartment you created\> to host the Visual Builder instance.

5. Click **Create Instance**.

<br>

![ ](./business_media/media/image70.png)

6. In **Name**, enter the Visual Builder instance's name.

Example: nl2sql_dev_vbcs

7. (Optional) In **Compartment**, select the compartment you created to host the Visual Builder instance. If you've selected the compartment in Step 4, ignore this step.

Example: genai-demos

8. Click **Create Visual Builder Instance**.

### VBCS Setup – User Access to VBCS Instance

#### Grant user access

1. Sign in to Oracle Cloud.

2. From the Infrastructure Console, click the navigation menu  !["Navigation menu icon"](./business_media/media/image36.png) in the top left corner, expand **Identity**, and then click **Domains**.

![ ](./business_media/media/identity-domain.png)


3. Click the **Oracle Identity Cloud Service** link.

4. From the Oracle Identity Cloud Service page, click **Oracle Cloud Services**.

![ ](./business_media/media/image73.png)


5.  Search and open IDCS app corresponding to the your VBCS instance

Search keyword example: nl2sql

![ ](./business_media/media/cloud-services.png)

6. Navigate to Application roles

![ ](./business_media/media/image75.png)

7. Select applicable role(s) such as Service Administrator, add users by clicking on Manage link

![ ](./business_media/media/service-admin.png)

### Deploy VBCS Applications

#### Deploy Applications

1. Applications:-

| Application | Example |
|----------------|-------------| 
| Main Application/Landing page | \<vbcs-askdata\> |
| Feedback application | \<vbcs-FeedbackSPA\> |
| Interactive Graph application | \<vbcs-InteractiveGraph\> |
| Table Graph UI | \<vbcs-Table_Graph_UI\> |

![ ](./business_media/media/image77.png)

**(you may need to zip the above folder for the main app before importing)**

- **Update** The VBCS application files are found in [vbcs_oda_archives](../../../vbcs_oda_archives/).
    - Navigate to vbcs_oda_archives and zip the respective applications
        - zip -r my-vb-app.zip ./<my-vb-app>
    - Import the zip to VBCS

![ ](./business_media/media/image78.png)

2.  Navigate to your Visual Applications Home page and click **Import**.

![ ](./business_media/media/image79.png)

3. Click **Application from file** in the Import dialog box.

![Description of homepage-importapp-dialog1.png follows](./business_media/media/image80.png)

4. Drag the visual application archive file on your local system into the dialog box. Alternatively, click the upload area in the dialog box and use the file browser to locate the archive on your local system.

5. Enter the Application Display Name and Application ID. Both fields are automatically populated based on the archive name, but you may want to modify the name as desired and the ID to be unique in your identity domain.

![ ](./business_media/media/image81.png)

6. Click **Import**.

### Update VBCS Applications

#### ODA URL, Channel ID, WebSocket, IDCS, Backend URL

1. After Importing**, Open main app** (vbcs_askdata)

Go to “main-start” 🡪 JavaScript (tab)

![ ](./business_media/media/image82.png)

2. Update ODA URL & Channel below

![ ](./business_media/media/oda-url.png)

![ ](./business_media/media/oda-url-2.png)

![ ](./business_media/media/websocket.png)

3. Next Go to server connections

#### Overview

 Click on link “IDCSBackend” under overview.

![ ](./business_media/media/image86.png)

![ ](./business_media/media/idcs-server.png)

![ ](./business_media/media/idcs-server-2.png)


Click on the pencil icon.

![ ](./business_media/media/idcs-server-3.png)

> Under Authentication:
> Update Username and Password (these are from confidential IDCS app – client id & secret).

![ ](./business_media/media/idcs-server-4.png)

![ ](./business_media/media/idcs-server-5.png)

![ ](./business_media/media/idcs-server-6.png)


> Also verify the Instance URL.

![ ](./business_media/media/idcs-server-7.png)


4.  Similarly**,** Open Interactive Graph app & Table-Graph app

Go to Services 🡪 Service Connections 🡪 interactive-graph (for Interactive Graph App)

Go to Services 🡪 Service Connections 🡪 interactiveTables (for Table_Graph App)

![ ](./business_media/media/interactive-tables.png)


Click on the pencil icon

![ ](./business_media/media/interactive-tables-2.png)


Verify/Edit the Instance URL. This points to APIGW. Therefore, this should match the APIGW url. 
\[Example, <https://apigw-url.apigateway.us-chicago-1.oci.customer-oci.com/v1>\]

Verify/Edit Authentication section. This should match the [IDCS confidential app](./business_idcs.md) that was setup earlier.

- Authentication: OAuth 2.0 Client Credentials
- Client ID & Secret: \<click pencil icon to enter client id and secret\>
- Scope: \<Example: urn:opc:idm:\_\_myscopes\_\_\> (if using same instructions from IDCS App, odatest)
- Token URL: \<Example:
<https://idcs-server.identity.oraclecloud.com/oauth2/v1/token>\>

- Connection Type: \<Example: Dynamic, the service does not support CORS\>

![ ](./business_media/media/api-gw-server.png)


### Stage VBCS Applications

#### Stage

Stage VBCS Applications.

**<u>Please note that the display names of the deployed VBCS applications might differ from those shown in the screenshot below.</u>**

![ ](./business_media/media/image97.png)


![ ](./business_media/media/image98.png)


If you are prompted with the following question, select “Stage application with a clean database”

![ ](./business_media/media/image99.png)

![ ](./business_media/media/image100.png)

![ ](./business_media/media/image101.png)

Make a note of URLs, especially Table_Graph app and InteractiveGraph app as you will need to specify the URLs in the properties file on the VM server.

### Edit VBCS Application URLs in VM1

#### Edit Table Graph and Interactive Graph URL in VM1

> SSH into VM1
>
> Edit file: /home/opc/<span class="mark">ConfigFile.properties</span>
>
> Goto the following section and edit,
>
> \[vbcs\]  
> endpoint.url=  
> graph_app.url=\<graph_app url\>/  
> idata_app.url=\<table_graph_app_url\>/
>
> Example:
>
> \[vbcs\]  
> endpoint.url=<https://your-vb-instance.builder.us-chicago-1.ocp.oraclecloud.com/ic/builder/rt/>  
> graph_app.url=vbcs_InteractiveGraph_pub_sec/1.0/webApps/nl2sql_interactivegraph/  
> idata_app.url=vbcs_Table_Graph_UI_pub_sec/1.0/webApps/dynamictabledata/
>
![ ](./business_media/media/server-config.png)

### Test Application

Once engine config is updated to include the above vb applications, and everything is configured correctly, you should be able to converse with AskData: 

![AskData](./images/askdata-app.png)

![AskData](./images/askdata-app-2.png)

> **Note** You can select "View Full Result Set" to open another visual interface 

![AskData](./images/askdata-app-3.png)

![AskData](./images/askdata-app-4.png)
## Private Resources

This section is applicable only if the target APIs accessed by ODA and
VBCS are in a private subnet. For example, if the APIs are fronted by a
private API Gateway. Otherwise, skip this section.

### Create ODA Private Endpoint using OCI Console

#### ODA Private Endpoint

By default, ODA can access only APIs which are publicly accessible from the Internet. Therefore, to access private resources located in OCI VCM or running in an on-prem envn or within other data centers, we need to enable private endpoint feature.

An ODA private endpoint is a private resource provisioned within your VCN and represents the Oracle Digital Assistant in this VCN. The Digital Assistant service sets up the private endpoint in a subnet of your choice within the VCN.

- To create an ODA private endpoint, open the hamburger menu, select Analytics & AI, then select Digital Assistant under AI Services.

!["Locate Digital Assistant in OCI Console hamburger menu"](./business_media/media/image103.jpeg)

- Once the Digital Assistant Instances page is opened, click “Private endpoints” and select “Create private endpoint”:

!["Create ODA private endpoint dialog"](./business_media/media/create-private-endpoint.jpeg)

- In the opened dialog you will need to select the compartment in which the ODA private endpoint should be managed, the virtual cloud network (VCN) and subnet in which the private endpoint should be created and the name of the private endpoint. Optionally you can specify the description, network security groups and tags.

- Once the ODA private endpoint is created, you can view its details.

!["Created ODA private endpoint details panel"](./business_media/media/private-endpoint-2.jpeg)


- In order to enable an ODA private endpoint to be used in Digital Assistant, you’ll need to associate this private endpoint with the Digital Assistant instance by clicking the “Associate ODA instance” button:

!["Associate ODA instance dialog"](./business_media/media/private-endpoint-3.jpeg)

### Update REST APIs to use Private Endpoint

#### REST APIs in ODA to use Private Endpoint

Sign in to your ODA console.

- Next click on “settings” as shown below

![](./business_media/media/image38.png)


Click on API Services -\> REST Services

You will see an option to enable Private Endpoint for this REST Service and to select one of the available private endpoints.

If you don’t see the Private Endpoint enablement option or list of available private endpoints is empty, then make sure you have associated the private endpoint with that ODA instance.


!["Select private endpoint for REST service"](./business_media/media/image107.jpeg)

Note that the private endpoint feature is not supported by the custom component of ODA. Therefore, you may create a public load balancer is such cases.


## Troubleshooting 

1. Graph isn't showing in Table Graph VB App
    - Solution: Make sure to assign user role to idcs group in app settings

## [Return home](../../../README.md)