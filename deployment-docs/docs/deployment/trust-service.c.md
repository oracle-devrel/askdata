# 1.1 Trust Services

### Prerequisites 

These instructions assume you have a VM running on Oracle Linux 8 or 9 and are able to ssh into it. 

## Environment Variables 

If you want to run or test the service manually, it is a good idea to set the environment variables, as they are used by the service. 

The environment parameters (example for dev)
``` bash
export NL2SQL_OCI_MODE=instance  
export NL2SQL_OCI_BUCKET=bucket  
export NL2SQL_OCI_NS=tenancy-namespace
export NL2SQL_ENV=dev
```

The configuration file is json based and lives on the object store

### Object Storage Configuration 

- Read from the object store  (\<bucket\>/\<env\>/config/trust-config.json)

<bucket>/
└── <env>/
    └── config/
        └── trust-config.json

- The location of the trust database wallet is readfrom the object store (\<bucket\>/\<env\>/wallet/wallet.zip)

<bucket>/
└── <env>/
    └── wallet/
        └── wallet.zip

# Network Configuration

- private subnet
- open 22, 8000

# VM Configuration

- Image:
  - To use: Oracle Linux 8, developer image. 
  - Legacy:: nl2sql-custom-image
- Deployed on private subnet
- 250 Gb boot drive
- VM.Standard.E4.Flex
- 32 Gb RAM
- 2 oCPU
- Agents
  - Custom Logs Monitoring
  - Compute Instance Run Command
  - Compute Instance Monitoring

# High-level Process
Here we describe the main steps to set the trust service vm

1. Create the Oracle Linux Machine (VM, Docker, etc...)
    1. Make it part of the OCI instance principal/dynamic group
    2. ssh key
    3. Deployed on private subnet
2. Setup the .bashrc
    1. Add the required environment variables
    2. Run source .bashrc after setting env variables
3. Add port 8000 (REST Service) to the firewall
4. Install the OracleDB and Python 3.11.11 or later.
5. Install pip
  - sudo dnf install python3.11-pip
  - sudo update-alternatives --install /usr/bin/pip pip /bin/pip3.11 40
  - which pip
  - pip --version
6. Copy the /rest directory & code to the trust VM
    1. Update the configuration file
7. Install the required python libraries
8. Set up the nl2sql_rest.service
    1. Make sure it is using the proper configuration file (dev, demo,
        local, etc...)
9. Ensure the supporting systems are available

# Dependency List
We list here the different systems and infrastructure to which we connect to. If we can't reach them or use them, the trust service can't be functional. As such, there is a validation step that ensure these elements are reachable.

| **Dependency**  | **Why**                          |
|-----------------|----------------------------------|
| Oracle Database | Persistence store for the system |
| LLM Engine      | Cohere based                     |
| OCI Client      | Object store, vault, etc...      |
| AI Model        | llama based                      |
| Vault           | Oracle DB Password               |
| Object Store    | Required bucket                  |

# Dependency Validation

The dependency validation is to make sure that the cloud accesses and external systems are reachable from the VM where the trust services are installed.

If needed to install the oci command line:

## Installing oci cli 
``` bash
pip install --upgrade pip setuptools setuptools-rust  
pip install oci  
sudo bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" \
  --accept-all-defaults \
  --install-dir /usr/local/bin \
  --exec-dir /usr/local/bin

# Add CLI to path  
export PATH="/usr/local/bin/oci-cli/bin:\$PATH"
```

# Dependency Validation Methods

| Dependency | Validation Method |
|:---|:---|
| oci object store | oci os get <bucket list> and make sure your bucket is in it. |
| oci vault | oci vault <db secret> |
| oci dac | <future> |
| nl2sql engine | `curl -vvv http://NLSQL_ENGINE_IP:PORT/getsql -H "Content-Type: application/json" -d '{"question": "Show me the project names"}'` <br>  `curl -vvv -X POST  "http://<nl2sql>:8001/getprompt" -H "Content-Type: application/json" -d '{"question": "Show me the project names"}'` |
| llm engine | |
| Database Validation | In the admin user _SELECT USER FROM DUAL;_ |

# Configuration File Parameters

Each of the group (except REST) inherits from the OCI group. When specified, a property can be redefined/overriden by the lower group if used by it.

| Group | Name | Description | Default value | Redefinable |
|:---|:---|:---|:---:|:---:|
| REST | location | The environment in which the system is deployed. dev,prod,prod1... | None | |
| OCI | auth_mode | (user/instance)<br>Used to control if the oci authentication is based on the instance principle.<br>When using instance principle, the config.xml file is not read. | user | |
| OCI | compartment.ocid | ocid of the compartement where the resource is located. | None | Yes |
| OCI | tenancy.ocid | ocid of the tenancy where the resource is located. | None | Yes |
| OCI | namespace | namespace of the compartement where the resource is located.<br><br>This is the name of the tenancy. | None | Yes |
| OCI | region | name of the region where the sources is. | None | Yes |
| AI MODEL | genai.url | | | |
| AI MODEL | genai.model_embed | | | |
| AI MODEL | genai.region | | The oci region | |
| AI MODEL | genai.engine_nl2sql_url | | | |
| VAULT | region | | The oci region | |
| VAULT | db.secret_ocid | ocid of the database password in the vault secret | | |
| OBJECT STORE | region | | The oci region | |
| OBJECT STORE | bucket.name | Name of the bucket that is the base for the data used by the application. Namely the metadata and the finetune information. | | |
| FINETUNE | os.path | Object Store path that is prepended to the file name. for example \<env\>/finetune/jsonl | | |
| FINETUNE | local.path | Location where the file is stored locally to the server. for example /home/opc/rest/upload | | |
| METADATA | file_name | name of the file where the metadata was. formerly "metadata_v2.json" | | |
| METADATA | os.path | for example \<env\>/config/ | | |
| METADATA | local.path | Location where the file is stored locally to the server. for example /home/opc/rest/conf | | |
| DATABASE | db.wallet | Location of the wallet directory. The wallet zip file needs to be expanded.<br><br>For example /home/opc/wallet/nl2sql-test | | |
| DATABASE | db.user | User that owns the tables (admin is used in development) | | |
| DATABASE | db.pwd | Password for the database. Will only work for the releases pre-dating Mid March 2025 | | |
| DATABASE | db.dns | Database DNS to use. For example, adb_low | | |
| DATABASE | db.datetime_format= | datetime format used by the database. | DD-MON-YYYY hh24:mi:ss | |
| DATABASE | db.date_format | date format used by the metrics. | DD-MON-YYYY | |
| METRICS | metric.start_date | base date for the metrics. 02/10/2025 in development. Should be set to the start date for the current system | | |
# Configuration Steps

The steps assume a basic image, as opposed to the custom image.

# Installation and Setup Steps

# NL2SQL Setup Guide

## 1. Create the Machine

Create a Oracle Linux 8 (or later) VM with the following specifications:
- If using OL-8, use the developer version
- If you are using Oracle Linux 9, also run:
  ```bash
  sudo yum install oraclelinux-developer-release-el9
  ```

**Automation:** Terraform

## 2. Required Environment Variables

Add the following environment variables to the user's bashrc:

```bash
export PYTHONPATH=/home/<user>/:.:
export NL2SQL_OCI_MODE=instance
export NL2SQL_OCI_BUCKET=bucket
export NL2SQL_OCI_NS=tenancy-namespace
export NL2SQL_ENV=dev
```

**Note:** The "dev" environment should be replaced with the appropriate environment tag. This is used in the formation of the path in the object store.

## 3. Set the Firewall

Configure the firewall to allow required ports:

```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --add-port=8000/tcp

sudo systemctl restart firewalld
```

**Automation:** Script

## 4. Install Oracle Thick Client

Install the Oracle Instant Client (ideally, follow the instructions according to the ADW version):

E.g. for 23ai

For Oracle Linux 8
```bash
sudo dnf install oracle-instantclient-release-23ai-el8
```
For Oracle Linux 9
```bash
sudo dnf install oracle-instantclient-release-23ai-el9
```

```bash
sudo yum install oracle-instantclient-sqlplus*
sudo yum install oracle-instantclient-tools*
```

Install sql client (linux 8 & 9)
```bash
sudo yum install oracle-instantclient-sqlplus
```

Install sql tools
```bash 
sudo yum install oracle-instantclient-tools
```

**Automation:** Script

## 5. Install Python

If you have installed the developer package, you should not need to do this. However, if you're having Python issues, you might have to work through the following:

```bash
sudo update-alternatives --config python
python -m pip install --upgrade pip
python -m ensurepip --default-pip
curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
python -m pip --version
sudo ln -sf $(which python) /usr/bin/pip
sudo ln -sf $(which python) /usr/bin/python3
sudo ln -sf $(which python) /usr/bin/pip
```

**Automation:** Script

## 6. Install Python Packages

Install the required Python packages using pip:

```bash
pip install pytest
pip install asyncio
pip install fastapi
pip install python-dateutil
pip install requests
pip install oci
pip install pandas
pip install psutil
pip install uvicorn
pip install oracledb
pip install httpx  # used for pytest
```

## 7. Copy Source Code

### Move Trust Files

Copy files in /rest/ directory to trust VM machine. 

**Process:** Manual

## 8. Update the Wallets

### Database Wallet Configuration

The database wallets need to be updated. Note that no files are provided for this, as it is generated as part of the installation.

1. Expand the wallet you have from the trust database you're connecting to
2. In the `ojdbc.property` file, ensure that it is using the TNS_ADMIN property:
   ```
   oracle.net.wallet_location=(SOURCE=(METHOD=FILE)(METHOD_DATA=(DIRECTORY=${TNS_ADMIN})))
   ```
3. In the `sqlnet.ora` file:
   ```
   WALLET_LOCATION = (SOURCE = (METHOD = file) (METHOD_DATA = (DIRECTORY=${TNS_ADMIN})))
   ```
4. Ensure that in the `trust-config.json` file, the `db.dns` property points to one of the ones defined in `tnsnames.ora`

> **NOTE**: The wallet will be pulled from the object storage bucket. Once validated with steps above, upload wallet to bucket. 

**Process:** Manual

## 9. Update the trust-config.json

Template for trust-config.json can be found under [/rest/nl2sql-trust/conf](../../../rest/nl2sql-trust/conf/trust_config.json)

1. Update the OCID and values to be used by the application according to the environment.

2. Upload the trust-config.json with updated values to the object storage bucket

> **NOTE**: For the wallet location in `trust-config.json`, provide the full path to the local machine of the trust vm. This will be where the script reads the wallet credentials, onced pulled from object storage.

> **NOTE**: The trust-config.json will be pulled from your object storage bucket. When running the script, this local file will be overwritten with the file in object storage.

> **NOTE**: Trust config expects dedicated ai cluster endpoint (dac)
  - On demand llama model endpoint can be provided instead instead (In case there is no dac on tenancy)

**Process:** Manual

## 10. Deploy the metadata.json File

The `metadata_v2.json` file needs to be placed in the object store in `<env>/config/metadata_v2.json` if it doesn't exist.

A template of the file is available in `/rest/nl2sql-trust/conf/metadata_v2.json`

**Note:** The file name can be anything, but it needs to be referenced in the `trust-config.json` file.

## 11. Setup the nl2sql Service

The `nl2sql_rest.service` can be found in /rest/script:

```bash
vi nl2sql_rest.dev.service  # update environment and other required changes
sudo cp ../script/nl2sql_rest.dev.service /etc/systemd/system/nl2sql_rest.service
./rest/script/restart_rest_service.sh
```

> **NOTE**: If unable to run restart script, make the script executable: 

```bash
$ chmod +x ./rest/script/restart_rest_service.sh
```

**Process:** Manual

## 12. Log Tracing

If you need to trace the log, there is a convenient script available:

```bash
./rest/script/trace.sh
```

# Validation

## Dependency and Infrastructure Validation

for all oci commands, ***use --auth instance_principal *** So it doesn't
look for an oci config file.

| Test | Description |
|------|-------------|
| `oci os object list -bn nl2sql --namespace-name <ns> --region <region> --auth instance_principal` | List the content of the bucket where the configurations are |
| `oci secrets secret-bundle get --secret-id <secret ocid> --auth instance_principal` | Obtain the databse secret |
| `sqlplus username/password@MYDB_ALIAS` | Connect to the trust database. |
| `curl -vvv http://<engine-ip>:8001/getsql -H "Content-Type: application/json" -d '{"question": "Show me the project names"}'` | Connect to the nl engine and provide a test sql |
| `curl -vvv prompt` | Connect to the engine and test prompt vectorization. |

## API Validation

All pytest files (python code) are distributed with the application
source code. We try to follow the principle that the test code should be
as a close as possible to the application. As such, only pytest is
required to test the application itself.

From nl2sql-trust directory:

| **Test** | **Description** |
|----|----|
| `pytest ui_routers/test_trust_operations.py` | test the ops live logs access |
| `pytest ui_routers/test_trust_metrics.py` | test the trust metrics calculations and access |
| `pytest ui_routers/test_administration.py` | test the ability to read the metadata file from the object store |

### Unit Functional Validation

| Test | Description |
|------|-------------|
| `pytest helpers/test_engine.py` | test the connection to the database by using the trust_library |
| `pytest helpers/test_llm.py` | test the instance principal setup<br>test the connection to the llm. **NOTE** Code needs to be changed depending on on-demand/dedicated model |
| `pytest helpers/test_oci_helper.py` | test the instance principal setup<br>test the vault, tag and object store |
| `pytest helpers/test_operations.py` | test the ops live logs access |
| `pytest helpers/test_trust_metrics.py` | test the trust metrics calculations and access |

### Debugging in case of Failure

1.  Running curl based on failed pytest.
2.  Running oci commands (os, secret, genai) based on failed pytest
3.  Running through the API Gateway ***(move to relevant page)***
    1.  Run the health curl.

##  Using APEX (And from LB)

| Validation | Expected behavior |
|:---|:---|
| `curl -X 'POST' 'http://localhost:8000/process_sql' -d '{"source": "auto"}'` | Tests the llm if there are records to process |
| `curl http://localhost:8000/admin_read_metadata_os` | Reads the metadata file from the object store |
| `curl http://localhost:8000/size_trust_library` | Accesses the database (and the vault) to obtain the information |
| `curl -vvv http://0.0.0.0:8000/get_logger_list` | Check that the REST system works without accessing external system. |
| `curl -vvv http://0.0.0.0:8000/health` (to be done) | Return a json file with each of the dependencies having been touched.<br><br>"healthCheck":<br>{<br>"database":"ok",<br>"llm_engine":"ok",<br>"llm_embeddings":"ok",<br>"object_store":"ok",<br>"vault":"ok"<br>} |

### Troubleshooting:
If unable to run oci commands, make sure shebang points to valid python executable e.g. python3.11

```bash 
sudo vi /usr/local/bin/oci
#!/usr/bin/python3.11
```

If process_sql validation command not working, try 

```bash 
curl -X POST 'http://localhost:8000/process_sql' \
     -H 'Content-Type: application/json' \
     -d '{"source": "auto"}'
```

If the APEX app stops working/lags after uploading a sample prompt file, try restarting the trust server. 

Problem: Graphs and charts not showing up in APEX Live Cert/ other pages

**Solution**: Trust LB must NOT have self-signed cert and REST_API variable should NOT have trailing "/"

Problem: ORA-12154: Cannot connect to database. Cannot find alias <adb>_low in /usr/lib/oracle/23/client64/lib/network/admin/tnsnames.ora.

**Solution**: Make sure your wallet directory is correct (ie, directory with tnsnames.ora).

## [Return home](../../../README.md)