#cloud-config
package_update: true
packages:
  - python3
  - python3-pip
  - curl
  - htop

write_files:
  - content: |
      [Unit]
      Description=${service_name} Service
      After=network.target
      
      [Service]
      Type=simple
      Environment=SERVICE_ENV=${service_env}
      Environment=SERVICE_PORT=${service_port}
      Environment=APP_VERSION=${app_version}
      Environment=PYTHONUNBUFFERED=1
      User=opc
      Group=opc
      WorkingDirectory=/home/opc
      ExecStart=/usr/bin/python3 /home/opc/${service_name}.py
      Restart=always
      RestartSec=10
      StandardOutput=journal
      StandardError=journal
      
      [Install]
      WantedBy=multi-user.target
    path: /etc/systemd/system/${service_name}.service
    permissions: '0644'

  - content: |
      #!/usr/bin/env python3
      import http.server
      import socketserver
      import os
      import json
      from datetime import datetime
      
      class SimpleHandler(http.server.BaseHTTPRequestHandler):
          def do_GET(self):
              self.send_response(200)
              self.send_header('Content-type', 'application/json')
              self.end_headers()
              
              response = {
                  'service': '${service_name}',
                  'environment': os.environ.get('SERVICE_ENV', 'unknown'),
                  'version': os.environ.get('APP_VERSION', 'unknown'),
                  'timestamp': datetime.now().isoformat(),
                  'message': 'Hello from Oracle Linux 9 VM!',
                  'path': self.path
              }
              
              self.wfile.write(json.dumps(response, indent=2).encode())
              
          def log_message(self, format, *args):
              print(f"[{datetime.now().isoformat()}] {format % args}")
      
      if __name__ == '__main__':
          PORT = int(os.environ.get('SERVICE_PORT', 8080))
          
          with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
              print(f"Starting ${service_name} service on port {PORT}")
              print(f"Environment: {os.environ.get('SERVICE_ENV', 'unknown')}")
              print(f"Version: {os.environ.get('APP_VERSION', 'unknown')}")
              httpd.serve_forever()
    path: /home/opc/${service_name}.py
    permissions: '0755'
    owner: opc:opc

runcmd:
  - systemctl daemon-reload
  - systemctl enable ${service_name}.service
  - systemctl start ${service_name}.service
  - systemctl status ${service_name}.service

final_message: |
  Cloud-init setup complete!
  Service: ${service_name}
  Environment: ${service_env}
  Port: ${service_port}
  Version: ${app_version}
  
  Check service status: sudo systemctl status ${service_name}
  View logs: sudo journalctl -u ${service_name} -f