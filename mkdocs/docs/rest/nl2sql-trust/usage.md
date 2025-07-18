# Running

Set the PYTHONPATH to the base of the code for example;

```
export PYTHONPATH=/home/ubuntu/git/nl2sql/rest/nl2sql-trust/:$PYTHONPATH
```

In both examples below, <b>`cd` to the rest directory</b>

To run on the server
```
nohup python np2sql_service.py --mode real --host 0.0.0.0 --port 8000 --ssl > np2sql_service.log 2>&1 &
```
To run locally
```
python np2sql_service.py --mode real --host 0.0.0.0 --port 8000 -v
```


# Accessing
Swagger UI: Go to http://IP:port/docs.

ReDoc: Go to http://IP:port/redoc.

# Testing (pytest)

The testing is done with pytest. <br>

|     File         |                                Description                           |
|------------------|----------------------------------------------------------------------|
|test_processor.py | This file is used to test the service without implicating the REST API. Both stub and real services are tested. |
|test_fastapi.py   | This file is used to test the external interfacing implementing the REST API. This is as close to test the API as we get without deploying a server.|
| test_finetune.py | This file is used to test the fine tuning export to the object store. |
|test_operations.py |This file is used to test the operations functionality from the web interface. |

# OpenSSL
Used to implement a self signed certificate for the fast_api application.
```
  openssl genpkey -algorithm RSA -out private.key
  openssl req -new -key private.key -out cert.csr
  openssl x509 -req -days 365 -in cert.csr -signkey private.key -out cert.pem
```
