For now, the installation to the server is simply the upload of the source from your working laptop.

To connect and upload to the vm : <br>

    ssh connection ssh -i ~/.ssh/ssh.key opc@207.xxx.xxx.xxx
    scp -i ~/.ssh/ssh.key -r ./rest  opc@207.xxx.xxx.xxx:~
    nohup python np2sql_service.py --mode real --host 0.0.0.0 --port 8000 > np2sql_service.log 2>&1 &
    
To run locally on my machine:

    export PYTHONPATH=/home/usr/git/nl2sql/rest/nl2sql-trust:$PYTHONPATH

