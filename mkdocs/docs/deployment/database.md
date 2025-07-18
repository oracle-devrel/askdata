# NL2SQL Database Deployment

## Creation
Done by the Terraform script

## Minimal Configuration
| Element | Size/Count| Comment |
|---------|-----------|---------|
| ECPU    | 2 | Minimal count |
| Disk    | 1 TB | Minimal count |

| Element |  Value  |
|---------|-----------|
| Workload type |Data Warehouse |
| WMinimum Version | 23ai |

## Configuration Check
- Should be private with public access (0.0.0.0/0 or more restrictive according to customer policy)
- Should have the private endpoint access configured.
- Should have APEX enabled

## Access
Should be done through a public load balancer