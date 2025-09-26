source /home/app/venv/bin/activate
export PYTHONPATH=.
python nl2sql_service.py --inst {$2} --host 0.0.0.0 --port 8000