## Create Service File
sudo vi /etc/systemd/system/nl2sql_rest.service
sudo cp nl2sql_rest.service /etc/systemd/system/nl2sql_rest.service

## File Content

Content of the service file

```
[Unit]
Description=NL2SQL REST Application
After=network.target  # Ensures network is up before starting the app

[Service]
Environment=PYTHONUNBUFFERED=1  # Optionally disable Python output buffering for immediate log entries
Environment=NL2SQL_ENV=local
Environment=NL2SQL_HOST=0.0.0.0
Environment=NL2SQL_PORT=8000
Environment=PYTHONPATH=/home/opc/:.

User=opc  # The user under which the service will run
Group=opc  # The group under which the service will run

WorkingDirectory=/home/opc/rest  # The directory where the app is located
ExecStart=/usr/bin/python /home/opc/rest/np2sql_service.py --inst $NL2SQL_ENV --host $NL2SQL_HOST --port $NL2SQL_PORT  # Command to start the app

Restart=always

StandardOutput=journal  # Send standard output to the systemd journal
StandardError=journal  # Send standard error to the systemd journal

[Install]
WantedBy=multi-user.target  # The service will start when the system reaches the multi-user run level
```

## To Manage
### Reload systemd to recognize the new service
sudo systemctl daemon-reload

### Start the FastAPI service
sudo systemctl start nl2sql_rest.service

### Stop the FastAPI service
sudo systemctl stop nl2sql_rest.service

### Enable it to start automatically on boot
sudo systemctl enable nl2sql_rest.service

### Disable it
sudo systemctl disable nl2sql_rest.service

### To restart the service
Note: Since this is started under opc, then the .bashrc variables are taken into account.
sudo systemctl restart nl2sql_rest.service

### View the logs of the service
sudo journalctl -u nl2sql_rest.service

To see it in real time
sudo journalctl -u nl2sql_rest.service -f

To clear the logs
sudo journalctl --vacuum-time=1s