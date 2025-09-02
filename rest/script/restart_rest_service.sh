sudo systemctl daemon-reload
sudo journalctl --vacuum-time=1s
sudo systemctl stop nl2sql_rest.service
sudo systemctl start nl2sql_rest.service
sudo journalctl -u nl2sql_rest.service -f
