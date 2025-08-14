## Oracle Digital Assistant (ODA)

### ODA Setup – Provision ODA Instance

#### Provision ODA Instance

1. Sign in to your Oracle Cloud account.

2. In the Infrastructure Console,
    click !["Navigation menu icon"](./business_media/media/image36.png) on the top left to open the navigation menu, select **Analytics & AI**,
    and select **Digital Assistant** (which appears under the **AI Services** category on the page).

3. From the **Compartments** panel, select a compartment.
4. Click **Create Digital Assistant Instance**.
5. On the **Create Digital Assistant Instance** page, fill in the following details:
    - **Compartment**. 
    - **Name**. Enter a name that reflects usage of the instance. For
      example, for a development environment, genai-nl2sql-dev
    - **Instance shape**. Select between the following shapes:
      - **Development**. This is a lightweight option that is geared
        toward development work.
      - **Production**. This option should be selected for production
        instances of Digital Assistant. In comparison with the
        Development shape, this option has higher rate limits and
        greater database capacity, which enables more Insights data to
        be collected.

![](./business_media/media/create-oda.png)

6. Click **Create**.

7. After a few minutes, your instance will go from the status
    of Creating to Active, meaning that your instance is ready to use.

### Deploy ODA Code – REST APIs

#### Import REST APIs

1. Sign in to your ODA console.

    - Next click on “settings” as shown below

![](./business_media/media/image38.png)

- Click on API Services -\> REST Services -\> Import REST Services

![](./business_media/media/image39.png)

##### Import the following REST services;

![](./business_media/media/image40.png)

- After import, for each of them, point them to api gateway url (do not
  change the trailing part of the URL like /v1/prompt in the example below)

![](./business_media/media/import-rest-services.png)

#### Select the location of API Gateway url

![](./business_media/media/api-gw.png)

### Deploy ODA Code – Authentication Service

#### Create Authentication Service

1. Sign in to your ODA console.

2. Next click on “settings” as shown below

![](./business_media/media/image38.png)

- Select Authentication Services from the list. Add new authentication service

![](./business_media/media/image43.png)

- Give IDCS URLs below

#### To find the hostname for the Domain in the IDCS URL

![](./business_media/media/domain-hostname.png)

> Grant Type: Authorization Code
>
> Identity Provider: Oracle Identity Cloud Services
>
> Token Endpoint URL: \<IDCS base url\>/oauth2/v1/token
> Authorization Endpoint URL: \<IDCS base url\>/oauth2/v1/authorize
> Client ID: \<Client Id from the IDCS confidential app\>
> Client Secret: \<Client Secret from the confidential app\>
>
> Scopes: urn:opc:idm:\_\_myscopes\_\_
> Subject Claims: sub
> Refresh Token Retention Period: 7

- Provide Client ID of IDCS & secret from IDCS confidential app below

![](./business_media/media/new-auth-service.png)

![](./business_media/media/new-auth-service-2.png)

### Deploy ODA Code – Skill

#### Import ODA Skill

1. Sign in to your ODA console.

    - Click Development -\> Skills

![](./business_media/media/image47.png)


- Click “Import Skill” (located right top corner):

![](./business_media/media/image48.png)


> Import the skill provided in vbcs_oda archives folder in the code:
>
![](./business_media/media/image49.png)


- After the skill is imported, you should see following under the list
  of skills: (actual name may differ)

![](./business_media/media/image50.png)


- Next Navigate your Skill

![](./business_media/media/image51.png)


- Go back to your skill and Train

![](./business_media/media/image52.png)

![](./business_media/media/image53.png)

### Update ODA Skill

#### Update REST API URL in the Custom Component

1.  Sign in to your ODA console.

    - Click Development -\> Skills
    - Open skill
    - Go to Skill’s Settings

![](./business_media/media/image54.png)

- Under Configuration tab 🡪 Custom Parameters 🡪 Edit postQueryURL

![](./business_media/media/image55.png)

>
> Replace URL
>
![](./business_media/media/replace-url.png)

>
> This will be the APIGW URL
>
> example:
> <https://api-host.apigateway.us-chicago-1.oci.customer-oci.com/v1/prompt>

#### Update Read Timeout for the Custom Component

1. Sign in to your ODA console.
    - Click Development -\> Skills
    - Open skill
    - Go to Skill’s Settings 🡪 General tab

![](./business_media/media/image57.png)

> Increase this value if a response from the backend system is expected
> to be longer than the specified value.

### Deploy ODA Code – Channel

#### Create ODA Channel

1. Sign in to your ODA console.

2. Create a Channel for your Skill

![](./business_media/media/image58.png)
>
![](./business_media/media/image59.png)
>
![](./business_media/media/channel-id.png)

- Make sure to enter “\*” for allowed domains if you would like to be accessible from anywhere.
- Make sure to note down channel id above.
- Also note on the main OCI page for ODA the base web url

![](./business_media/media/image61.png)
>
> Or
>
![](./business_media/media/oda-host.png)

- Finally configure the Channel to use the published Skill:

![](./business_media/media/image63.png)
>
>
![](./business_media/media/image64.png)

### Pay attention on Channel Creation
- **Make sure to enable the channel upon creation. It is disabled by default.**

- **Also make sure “Client Authentication Enabled” is disabled. It is enabled by default.**

![](./business_media/media/client-auth.png)

### Update Confidential App

#### Update Redirect URL

> Go back to Confidential App to replace the Redirect URL value with ODA base url concatenated with connector string.
>
> Format:
> To find ODA url
>
![](./business_media/media/redirect-url.png)
>
![](./business_media/media/redirect-url-2.png)

## Application Customization

> **This is optional.**

### Edit ODA Skill

#### Customize Greetings

To customize initial greeting message-

![](./business_media/media/image120.png)

> Open ODA Skill

Select Flow Designer 🡪 greetingsFlow

![](./business_media/media/image121.png)

Open component, Greetings

![](./business_media/media/image122.png)

Edit the messages field.

#### Customize Domain areas

To customize the following list -

![](./business_media/media/image123.png)

Open ODA Skill

Select Entities 🡪 Modules

![](./business_media/media/image124.png)

Add new values and delete existing values

![](./business_media/media/image125.png)

![](./business_media/media/image126.png)

#### Update Routing & example prompts

To update the routing rules & example prompts-

![](./business_media/media/image127.png)

Edit each of the highlighted send message components.

![](./business_media/media/image128.png)

![](./business_media/media/image129.png)

![](./business_media/media/image130.png)

Edit Switch Activity to update routing

![](./business_media/media/image131.png)

![](./business_media/media/image132.png)

🡪🡪 ![](./business_media/media/image133.png)

**Remember to retrain the skill**

![](./business_media/media/image134.png)
