# TITLE

[![License: UPL](https://img.shields.io/badge/license-UPL-green)](https://img.shields.io/badge/license-UPL-green) [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=oracle-devrel_test)](https://sonarcloud.io/dashboard?id=oracle-devrel_test)

## THIS IS A NEW, BLANK REPO THAT IS NOT READY FOR USE YET.  PLEASE CHECK BACK SOON!

## Introduction
MISSING

## Getting Started
MISSING

### Prerequisites
MISSING

## Notes/Issues
MISSING

## URLs
* Nothing at this time

## Contributing
<!-- If your project has specific contribution requirements, update the
    CONTRIBUTING.md file to ensure those requirements are clearly explained. -->

This project welcomes contributions from the community. Before submitting a pull
request, please [review our contribution guide](./CONTRIBUTING.md).

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security
vulnerability disclosure process.

## License
Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE.txt) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK. 
## Deployment Steps

1. Deploy Terraform Script
2. Configure Business App
    - Configure Business DB
    - Configure Trust DB
3. Configure IDCS App
4. Configure API Gateway
5. Configure Trust App
6. Configure ODA Skills
7. Configure VB Apps 

### TBD 
8. Deploy Trust Framework
9. Deploy APEX

## Overview

I ran a dry deployment using the cleaned repo on our tenancy. Listed are some of my findings & outstanding questions. 

- I was able to get the client business app deployed on our tenancy. A few things I noticed - 
    - The code expects a llama model, at least for the on demand configuration
    - Would have to be refactored if using e.g. cohere on demand 
- The existing documentation suggests deploying api gateway on private subnet due to lack of authentication. 
    - I was able to deploy the api gateway on public subnet with oauth2.0 authentication to idcs server and invoke from oda with token, so not sure why private subnet deployment for api gateway is suggested
- The existing code expects api keys and wallets configured directly on the server, at least for the client business engine 
- Redis is required but no instructions given 
- There was no example data given for the vendors table, so I exported the table from the main deployment as a csv and imported to ours
    - Vendors table is for client business db 
    - How do we want to provide this csv?
- The business app is dependent on the trust db (trust library), i.e. the trusted prompts, which isn't intuitive 
    - The code expects the TRUST_LIBRARY table to have at least one entry, otherwise it bombs 
    - I provided a sample entry in the sql file 
The sql for the client business db is outside the clientapp directory, & there are no instructions given on which db to upload to (upload to business db)

The business app is exposed on an API Gateway with the main entry /prompt, which maps to <business-app-ip>:8000... this will be used by ODA app.

There are a handful of files required and provided within the repo, but no instructions on how/when to use them. 
Examples include : 
1. Under sql, nl2sql_datamodel_schema.sql needds to be ran in the trust database 
    - Was able to run the client engine without the sql/sample_setup_ras.sql file. 
    - This is a prequisite to run the business client engine, which isn't intuitive 
2. Within the rest (trust) directory there are docker files... I think we can remove these? 
    - Haven't tested full trust deployment yet.

Some files I don't think are necessary at all 
1. autoprompt 
2. mkdocs... this is documentation we can perhaps repurpose (at least the md files)

Below are the various requirements and findings from deploying the infrastructure components on our tenancy - 

### ODA 

1. Configure IDCS Server first 
    - ODA skill expects a token to execute
    - Configured manually for now. Expects ODA client callback to work
2. Configured API gateway with nl2sql engine backend - provide api gateway endpoint in skill
    - Configured bearer token with IDCS app 
3. There are two skill zips that don't seem to be used and not referenced in the documentation - 
    - oda-skill-EmbeddedCont.changeit.zip
    - oda-skill-ExtOracleFn.changeit.zip 

### VBCS 

1. The zipped askdata vbcs app in here looks to be outdated. 
    - It's a more simple implementation, which might be best for now
2. Reference to websocket - to be deprecated? Need to test if working without 
    - Tested, seems to be unnecessary
3. App import relies on various images in the directory... do we want to provide these images in the repo?
    - I'm going to include them for now, since they are dependencies

### API Gateway 
1. API Gateway is configured with Single Authentication OAuth2.0 which requires a vault. 
2. The existing mkdocs documentation said to deploy the api gateway to private subnet due to lack of authentication... authentication can be added to api gateway on public subnet 

### Redis 
1. Redis is required but there were no instructions given on configuration

### Generative AI 
1. Existing deployment was using dedicated ai cluster/data science. I was able to get it to work with on demand model. 
    - Code is hard coded to handle only the llama models. Cohere models would require refactoring. 

### NL2SQL Business Engine 
1. The code is currently expecting the user to upload their own api keys 
2. Database wallets need to be uploaded manually 
3. png files trusted & untrusted.png are required to run the server.
4. autoprompt - need to test if working without (deprecated?)

### Client Database
1. The vendors table didn't have any example data. I had to export the table from the existing implementation and import as csv 
    - Do we want to include this csv in the repo, or add to object storage bucket and provide link? 

### Trust Database
1. Engine code expects at least one entry in Trust library table before execution
    - Provided an example entry with sample embedding

### Trust REST Framework
Haven't gotten this far, but the basic prompt endpoint does use the trust library table. 

## APEX
tbd ... do we want to include this in the first version? 

