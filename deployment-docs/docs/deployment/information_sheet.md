# Deployment Information Sheet

Before deploying the system, we need to gather the information necessary for the deployment on a specific environment.

## High-level Process

When first establishing the team to support and deploy the system, each of the roles and person should be identity namely for;

- System Administration
- System Deployment
- Application Support
- Cloud Support

## Dependency List

These are elements that must be available before you get started. More details will be required, but this will give you the basic starting point.

- An oracle cloud account with sufficient leeway to allocate the required resources.
- Domain Name for the askdata system
- Administrative Contacts (name, email, role)

## Network Configuration

As needed per components. 

## Configuration Steps

| Name | Description | Automation |
|------|-------------|------------|
|Domain Name | This will provide the persona of the nl2sql deployment. This in most situation should already exist for the customers. AskData is often used.||
|Trust Load Balancer Short Name | The short name is added to the deployment domain name. This is used to form the FQDN.||
|Apex trust load balancer short name | The short name is added to the deployment domain name for the apex hosting database. This results in the the FQDN ||
|Landing Zone Base Compartment | The base compartment for the landing zone is the container that will define all the groups.||
|nl2sql_env value | nl2sql_env is a freeform tag used to be able to query all resources used in a single nl2sql deployment. ||
|Trust Application Users | Need to gather the names and emails of the expert users to use the trust application. They need to be part of XXX group. The users need to receive an email telling them how to authenticate with the application in their environment.||
| Business User Identity Integration| We need to define how the business users will have their identity serviced. ||
| Customer Readyness |The customer requirement and information pertaining to this system needs to be defined and documented prior to any deployment.(Refer to customer facing configuration) ||

# Validation

Manual review and comparison to the required terraform variables.

## [Return home](../../../README.md)