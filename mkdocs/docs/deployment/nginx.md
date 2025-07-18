# Install NGINX for internal documentation

``` bash
sudo apt update && sudo apt install nginx
sudo dnf install nginx
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --add-port=9000/tcp
sudo vim /etc/nginx/conf.d/docs.conf
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Monitoring
``` bash
systemctl status nginx.service
journalctl -xe
sudo journalctl -u nginx.service -n 500
```

## Restarting NGINX
``` bash
sudo systemctl daemon-reload
sudo systemctl restart nginx
sudo journalctl -u nginx.service -n 500
sudo tail -f /var/log/nginx/error.log
```

## Moving the html pages
``` bash
sudo mkdir -p /var/www/docs
sudo cp -r /home/opc/docs/* /var/www/docs/
sudo chown -R nginx:nginx /var/www/docs
sudo chmod -R 755 /var/www/docs
````
