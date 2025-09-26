# Generic Information

# High-level Process

1.  Define a user defined tag (nl2sql_env={env} )that will be place on all resources.
2.  Define a log group that will be used for all resources (nl2sql_{groupname})
3.  Acquire Internet Domain unless you reuse an existing one.
4.  Identify Certificate Authority
    1.  As part of the development, we use let's encrypt
5.  Configure base DNS Zone (and name servers)
6.  Create containing compartment
7.  Gather required information
8.  Provide admin access or have a tenancy administator do the action.
9.  Run resource manager for the landing zone
10. DNS Configuration with the Internet domain
11. Object Store Information (in nl2sql bucket)
    1.  trust application configuration file.
    2.  trust metadata file
    3.  Database wallet.

# Dependency List

    Domain information

# Network Configuration

1.  Requires domain
2.  Create containing  compartment for hosting the landing zone.

# Included with the Landing Zone

| **Resource** | **Description** |
|--------------|-----------------|
| Bastion      | ssh proxy       |

### IAM Policies
| **Resource** | **Why** | **Policy** |
|--------------|---------|------------|
|              |         |            |

### Dynamic Groups

Add all trust and business vms to your dynamic group. An instance can be added with the following: 

```md
instance.id = 'ocid1.instance.oc1.us-chicago-1.xxx'
```

### Policies

Once the resources are added to the dynamic group, add the following policies.

The compartment name is the compartment where the resource resides.

- nl2sql-instance_principle, the application requires access to multiple services to obtain the information it requires to work.
    ```
    Allow dynamic-group <group-name> to read vaults in compartment <compartment-name>
    Allow dynamic-group <group-name> to read secrets in compartment <compartment-name>
    Allow dynamic-group <group-name> to manage objects in compartment <compartment-name>
    Allow dynamic-group <group-name> to read buckets in compartment <compartment-name>
    Allow dynamic-group <group-name> to manage secret-family in compartment <compartment-name>
    Allow dynamic-group <group-name> to read tags in compartment <compartment-name>
    Allow dynamic-group <group-name> to manage generative-ai-family in compartment <compartment-name>
    ```

- nl2sql-apigateway, the api gateway requires the policies to access the security vault when using oAuth.
    ```
    Allow dynamic-group <group-name> to read vaults in compartment <compartment-name>
    Allow dynamic-group <group-name> to read secrets in compartment <compartment-name>
    ```

- For a future release. Not needed yet.
    ```
    Allow dynamic-group <group-name> to manage certificates in compartment <compartment-name>
    Allow dynamic-group <group-name> to read certificates in compartment <compartment-name>
    ```

# Configuration Steps

| Name            |            Description                                 | 
|-----------------|--------------------------------------------------------|
| Internet Domain | Acquire/use internet domain name                       |
| Logging groups  | Define a logging group unique to this installation     |
| Custom Tag      | Define a custom tag nl2sql_<env> unique to this  installation. Use on all resources |
| DNS             | Create a nl2sql_<env> dns zone                         |
| Base Compartement| Creation of the compartment that will contain the rest of the services. |
| Landing Zone    | Run Landing Zone for the initial configuration         |
| Object Store    | Create Required buckets  nl2sql                                 |

# Validation

Not at this time.

## [Return home](../../../README.md)