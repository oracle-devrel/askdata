# Why a Reverse Proxy?

In preparation for the use of a JWT Token (oAuth enabling).
This is mostly for documentation only. Using the API Gateway, it serves this purpose.
What would be needed to is to make sure that this can only be accessed through the private network.

# Package install
sudo apt update
sudo apt install nginx

# Configuration
## File
sudo vi /etc/nginx/sites-available/n2sql_rest

# Configuration
```
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
# Enable and Reload

```
sudo ln -s /etc/nginx/sites-available/n2sql_rest /etc/nginx/sites-enabled/

sudo systemctl reload nginx
```
