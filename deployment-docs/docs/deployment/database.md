# NL2SQL Database Deployment

## Creation
Manual 

For basic instructions on deploying an autonomous database, see [Autonomous Database 15 Minute Quickstart](https://livelabs.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=928&p210_wec=&session=110849810147522)

## Minimal Configuration
| Element | Size/Count| Comment |
|---------|-----------|---------|
| ECPU    | 2 | Minimal count |
| Disk    | 1 TB | Minimal count |

| Element |  Value  |
|---------|-----------|
| Workload type | Data Warehouse |
| Minimum Version | 23ai |

## Configuration Steps 
- Provision one database for client/business db 
    - [Create ACCOUNT_PAYABLES_TBL](../../../sql/tbl_ddl.sql)
    - Populate ACCOUNT_PAYABLES_TBL table 
        - Execute [sql/demodata.sql](../../../sql/demodata.sql) for demo data 
    - VENDORS table 
        - [Vendors CSV](../../../clientApp/vendors-export.csv)
        - Upload manually through sql developer
            - **Note** Any example data that coincides with real businesses is coincidental. 
- Provision one database for trust db 
    - [Create Trust DB Tables](../../../sql/nl2sql_datamodel_schema.sql)
    - TRUST_LIBRARY table will be used by business and trust applications
    - Engine requires at least one entry in TRUST_LIBRARY table
        - Sample entry given in [sql/nl2sql_datamodel_schema.sql](../../../sql/nl2sql_datamodel_schema.sql)
    - Execute nl2sql_datamodel_schema.sql on trust db

> **Note** Make sure to execute all commands in sql scripts on respective databases as mentioned above

### Private Access (optional)
- Should be private with public access (0.0.0.0/0 or more restrictive according to customer policy)
- Should have the private endpoint access configured.
- Should have APEX enabled

#### Access
Should be done through a public load balancer. See [Private LB for ADW](../deployment/apex-private-adw-lb.md)