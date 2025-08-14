# AskData NL2SQL Engine

[![License: UPL](https://img.shields.io/badge/license-UPL-green)](https://img.shields.io/badge/license-UPL-green) [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=oracle-devrel_test)](https://sonarcloud.io/dashboard?id=oracle-devrel_test)

## Introduction

[Introduction](deployment-docs/docs/deployment/introduction.md)

## Getting Started
Start with familiarizing yourself with the [Architecture](deployment-docs/docs/deployment/architecture.md) & [Introduction](deployment-docs/docs/deployment/introduction.md)

For policies see [Defining Policies](deployment-docs/docs/deployment/generic.md)

The CIS Landing Zone is optional but helps with providing a sandbox environment with best practices
[Deploy CIS LZ](deployment-docs/docs/deployment/landing_zone.md)

### Prerequisites
This solution assumes you have access to an OCI tenancy with the admin ability to provision the following resources: 
- VBCS 
    - [Deploy VBCS](deployment-docs/docs/deployment/VBCS.md)
- ODA
    - [Deploy ODA](deployment-docs/docs/deployment/oda.md)
- IAM Confidential App 
    - [Deploy IAM App](deployment-docs/docs/deployment/business_idcs.md)
- Vault
    - [Deploy Vault](deployment-docs/docs/deployment/vault.md)
- API Gateway
    - [Deploy API Gateway](deployment-docs/docs/deployment/business_api_gateway.md)
- Business (client) ADW database
    - [Deploy Database](deployment-docs/docs/deployment/database.md)
- Trust ADB database
    - [Deploy Database](deployment-docs/docs/deployment/database.md)
- Redis Cache 
- VCN 
    - Two VMs, one for engine in private sn and one bastion/jump host 
        - [Deploy Engine Documentation](deployment-docs/docs/deployment/nl2sql_engine.md)

## Deployment Steps

1. Configure Business App
    - Configure Business DB
    - Configure Trust DB
2. Configure IDCS App
3. Configure API Gateway
4. Configure ODA Skills
5. Configure VB Apps 

## Notes/Issues

See [Troubleshooting](deployment-docs/docs/deployment/architecture.md)

This first release is focused on deploying the NL Engine/ClientApp for the business user. The Trust Framework plans to be added next release. However, documentation is available under [Deployment](deployment-docs/docs/deployment/)
if you'd like to get familiar. All documentation related to apex & trust service would be for the trust framework. 

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
