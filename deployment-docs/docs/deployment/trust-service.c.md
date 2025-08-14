# 1.1 Trust Services

If you want to run or test the service manually, it is a good idea to set the environment variables, as they are used by the service. 

The environment parameters (example for dev)
``` bash
export NL2SQL_OCI_MODE=instance  
export NL2SQL_OCI_BUCKET=bucket  
export NL2SQL_OCI_NS=tenancy-namespace
export NL2SQL_ENV=dev
```

The configuration file is json based and lives on the object store

- Read from the object store  (\<bucket\>/\<env\>/config/trust-config.json)

- The location of the trust database wallet is readfrom the object store (\<bucket\>/\<env\>/wallet/wallet.zip)

# Network Configuration

- private subnet
- open 22, 8000, 8888

# VM Configuration

- Image:
  - To use: Oracle Linux 8, developer image. 
  - Legacy:: nl2sql-custom-image

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
    1. Make it part of the OCI instance principal
    2. ssh key?
2. Setup the .bashrc
    1. Add the required environment variables
3. Add ports 8000 (REST Service) and 8888 (mkdocs) to the firewall
4. Install the OracleDB and Python 3.11.11 or later.
5. Install pip
6. Copy the required source code release from the artifact registry
    1. Update the configuration file
7. install the required python libraries
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
bash -c "\$(curl -L <https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh>)"
   -- \\  
   --accept-all-defaults \\  
   --install-dir /usr/local/bin \\  
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
| nl2sql engine | `curl -vvv http://NLSQL_ENGINE_IP:PORT/getsql -H "Content-Type: application/json" -d '{"question": "Show me the project names"}'` <br>  `curl -vvv http://NLSQL_ENGINE_IP:PORT/getprompt" -H "Content-Type: application/json"` |
| llm engine | |
| Database Validation | In the admin user _SELECT USER FROM DUAL;_ |

# Configuration File Parameters

Each of the group (except REST) inherits from the OCI group. When specify, a property can be redefined/overriden by the lower group if used by it.

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
export NL2SQL_OCI_MODE=instance_principle
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
sudo firewall-cmd --permanent --add-port=8888/tcp
sudo firewall-cmd --add-port=8888/tcp
```

**Automation:** Script

## 4. Install Oracle Thick Client

Install the Oracle Instant Client (ideally, follow the instructions according to the ADW version):

```bash
sudo yum install oracle-instantclient-sqlplus*
sudo yum install oracle-instantclient-tools*
```

**Automation:** Script

## 5. Install Python

**Note:** This should not be necessary with the proper image and needs cleanup.

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
pip install dotmap
pip install requests
pip install oci
pip install pandas
pip install psutil
pip install uvicorn
pip install oracledb
pip install httpx  # used for pytest
```

## 7. Install Pytest

```bash
pip install pytest
```

## 8. Copy Source Code

### Unpack Zip File

link to artifactory here. Not sure if needed. 

The artifacts are organized in versions, like 2025W21. Download the corresponding source to match the other artifacts you are using.

**Process:** Manual

## 9. Update the Wallets

**Note:** Not needed starting with version 2025W22

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

**Process:** Manual

## 10. Update the trust-config.json

Copy the proper release for `trust-config.json` from <another link to artifactory>

Update the OCID and values to be used by the application according to the environment.

**Process:** Manual

## 11. Deploy the metadata.json File

The `metadata.json` file needs to be placed in the object store in `<env>/config/metadata.json` if it doesn't exist.

**Note:** The file name can be anything, but it needs to be referenced in the `trust-config.json` file.

## 12. Setup the nl2sql Service

Use the attached file `nl2sql_rest.service`:

```bash
vi nl2sql_rest.dev.service  # update environment and other required changes
sudo cp ../script/nl2sql_rest.dev.service /etc/systemd/system/nl2sql_rest.service
./rest/script/restart_rest_service.sh
```

**Process:** Manual

## 13. Log Tracing

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
| `oci os object list -bn nl2sql --namespace-name <ns> --region <region>` | List the content of the bucket where the configurations are |
| `oci secrets secret-bundle get --secret-id <secret ocid>` | Obtain the databse secret |
| `sqlplus username/password@MYDB_ALIAS` | Connect to the trust database. |
| `curl -vvv 'http://<engine url:8002>/getsql'`<br>`-H 'accept: application/json'`<br>`-H 'Content-Type: application/json'`<br>`-d '{"question": "show dealer names and addresses"}'` | Connect to the nl engine and provide a test sql |
| `curl -vvv prompt` | Connect to the engine and test prompt vectorization. |

## API Validation

All pytest files (python code) are distributed with the application
source code. We try to follow the principle that the test code should be
as a close as possible to the application. As such, only pytest is
required to test the application itself.

**Note: Starting with the version 2025W22, the <u>app</u> directory is
renamed <u>ui_routers</u> directory to avoid a conflict.**

| **Test** | **Description** |
|----|----|
| `pytest -m app/test_trust_operations.py` | test the ops live logs access |
| `pytest -m app/test_trust_metrics.py` | test the trust metrics calculations and access |
| `pytest -m app/test_administration.py` | test the ability to read the metadata file from the object store |

### Unit Functional Validation

| Test | Description |
|------|-------------|
| `pytest -m helpers/test_engine.py` | test the connection to the database by using the trust_library |
| `pytest -m helpers/test_llm.py` | test the instance principal setup<br>test the connection to the llm |
| `pytest -m helpers/test_oci_helper.py` | test the instance principal setup<br>test the vault, tag and object store |
| `pytest -m helpers/test_operations.py` | test the ops live logs access |
| `pytest -m helpers/test_trust_metrics.py` | test the trust metrics calculations and access |

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
| `curl -vvv http://0.0.0.0:8000/healthcheck` (to be done) | Return a json file with each of the dependencies having been touched.<br><br>"healthCheck":<br>{<br>"database":"ok",<br>"llm_engine":"ok",<br>"llm_embeddings":"ok",<br>"object_store":"ok",<br>"vault":"ok"<br>} |