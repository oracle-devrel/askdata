source /home/app/venv/bin/activate
export PYTHONUNBUFFERED=1
export PYTHONPATH=/home/app/:/home/app/rest/nl2sql-trust
cd /home/app/rest/nl2sql-trust/
python nl2sql_service.py --inst $NL2SQL_ENV --host $NL2SQL_HOST --port $NL2SQL_PORT