# AskData NL2SQL Engine

[![License: UPL](https://img.shields.io/badge/license-UPL-green)](https://img.shields.io/badge/license-UPL-green) [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=oracle-devrel_test)](https://sonarcloud.io/dashboard?id=oracle-devrel_test)

## Introduction

Oracle AskData is a conversational AI platform powered by Oracle Generative AI. With AskData, you can ask natural language questions like "Give me all past due invoices" or "Show me sales for last week over $100,000" and get instant, accurate results. 

The solution empowers both non-technical users and SQL experts by simplifying complex queries and freeing up time for deeper analysis and decision-making.


## Getting Started
Please see the [Introduction](deployment-docs/docs/deployment/introduction.md) & [Architecture](deployment-docs/docs/deployment/architecture.md) 

For policies see [Defining Policies](deployment-docs/docs/deployment/generic.md#dynamic-groups)

### Prerequisites
The CIS Landing Zone is optional but helps with providing a sandbox environment with best practices

- [Deploy CIS LZ](deployment-docs/docs/deployment/landing_zone.md)


This solution assumes you have access to an OCI tenancy with the admin ability to provision the following resources: 

- IDCS/IAM Confidential App 
    - [Deploy IAM App](deployment-docs/docs/deployment/business_idcs.md)
- Vault
    - [Deploy Vault](deployment-docs/docs/deployment/vault.md)
- Business (Client) ADB database
    - [Deploy Database](deployment-docs/docs/deployment/database.md)
- Trust ADB database
    - [Deploy Database](deployment-docs/docs/deployment/database.md)
- OCI Cache 
    - [Deploy OCI Cache Cluster](https://docs.oracle.com/en-us/iaas/Content/ocicache/createcluster.htm#top) 
- VCN 
    - Private Subnet
    - Public Subnet 
    - [Deploy a VCN](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/quickstartnetworking.htm#Virtual_Networking_Quickstart)
- Two VMs
    - Engine 
        - [Deploy Engine Documentation](deployment-docs/docs/deployment/nl2sql_engine.md)
    - Bastion/jump host
        - To access engine in private subnet
- API Gateway
    - [Deploy API Gateway](deployment-docs/docs/deployment/business_api_gateway.md)
    - (Optional) If deploying API Gateway privately, see [ADW API Gateway Private Access](deployment-docs/docs/deployment/adw_private.md)
- VBCS 
    - [Deploy VBCS](deployment-docs/docs/deployment/VBCS.md)
- ODA
    - [Deploy ODA](deployment-docs/docs/deployment/oda.md)
## Deployment Steps

1. Configure Business DB
2. Configure Trust DB
3. Configure IDCS App
4. Configure OCI Cache
4. Configure Engine 
5. Configure API Gateway
6. Configure ODA Skills
7. Configure VB Apps 

### Validation 

[Validation Testing](deployment-docs/docs/deployment/validation.md)

## Notes/Issues

See [Troubleshooting](deployment-docs/docs/deployment/troubleshooting.md)

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
