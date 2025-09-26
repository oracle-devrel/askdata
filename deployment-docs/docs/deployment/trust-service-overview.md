# NL2 SQL Trust Services Deployment

# Introduction
## Update from the previous installation method.
The main structural differences in this release when compared to version 1.0 are:

The environment parameters (example for dev)
+ NL2SQL_OCI_MODE=instance
+ NL2SQL_OCI_BUCKET=bucket
+ NL2SQL_OCI_NS=tenancy-namespace
+ NL2SQL_ENV=dev

The location and format of the trust-config file :
+ Now JSON based
+ Read from the object store (<bucket>/<env>/config/trust-config.json)

The location of the trust database wallet:
+ zip file (updated with the instructions below)
+ Read from the object store (location in the trust-config.json file (<bucket>/<env>/wallet/wallet.zip))

# Technology
+ Virtual Machine on Oracle OCI
+ Python 3.11.11
+ Bash scripts

# Configuration

## Network Configuration

+ private subnet
+ open 22, 8000

## VM Configuration
+ Image to use: Oracle Linux 8, developer image. 
+ 250 Gb boot drive
+ VM.Standard.E4.Flex
+ 32 Gb RAM
+ 2 oCPU
### Agents
+ Custom Logs Monitoring
+ Compute Instance Run Command
+ Compute Instance Monitoring

# High-level Process
- Create the Oracle Linux Machine (VM, Docker, etc...)
- Make it part of the OCI instance principal
- Deploy your management ssh key
- Setup the .bashrc
  - Add the required environment variables
- Add port 8000 (REST Service) to the firewall
- Install the OracleDB and Python 3.11.11 or later.
  - Install pip
- Copy the required source code from /rest/nl2sql-trust & /rest/scripts
  - Update the trust-config.json configuration file
  - Upload trust-config.json to object storage
  - install the required python libraries
  - Set up the nl2sql_rest.service
  - Make sure it is using the proper configuration file (dev, demo, local, etc...)
  - Ensure the supporting systems are available

  ## [Return home](../../../README.md)