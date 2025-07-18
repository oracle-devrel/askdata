#cloud-config
package_update: true
package_upgrade: true

# Install basic packages first
packages:
  - unzip
  - curl
  - python3.11
  - python3.11-pip

#Note: The user opc doesn't exist when doing write_files.

write_files:
  - content: |
      [Unit]
      Description=NL2SQL REST Application
      After=network.target
      [Service]
      Environment=PYTHONUNBUFFERED=1
      Environment=NL2SQL_ENV=${nl2sql_env}
      Environment=NL2SQL_HOST=0.0.0.0
      Environment=NL2SQL_PORT=${nl2sql_port}
      Environment=NL2SQL_OCI_MODE=instance
      Environment=NL2SQL_OCI_NS=${namespace}
      Environment=NL2SQL_OCI_BUCKET=${nl2sql_bucket}
      Environment=PYTHONPATH=/home/opc/:.
      User=opc
      Group=opc
      WorkingDirectory=/home/opc/rest/nl2sql-trust
      ExecStart=/home/opc/venv/bin/python /home/opc/rest/nl2sql-trust/nl2sql_service.py --inst $NL2SQL_ENV --host $NL2SQL_HOST --port $NL2SQL_PORT
      Restart=always
      StandardOutput=journal
      StandardError=journal
      [Install]
      WantedBy=multi-user.target
    path: /etc/systemd/system/nl2sql_rest.service
    permissions: '0644'

  - content: |
      # NL2SQL Environment Variables
      export NL2SQL_OCI_MODE=instance
      export NL2SQL_OCI_BUCKET=${nl2sql_bucket}
      export NL2SQL_HOST=0.0.0.0
      export NL2SQL_PORT=${nl2sql_port}
      export NL2SQL_OCI_NS=${namespace}
      export NL2SQL_ENV=${nl2sql_env}
      export PYTHONPATH=/home/opc/:.
      
      # Oracle Instant Client
      export LD_LIBRARY_PATH="/opt/oracle/instantclient_23_4:$${LD_LIBRARY_PATH:-}"
      export PATH="/opt/oracle/instantclient_23_4:$${PATH:-}"
      
      # OCI CLI and Virtual Environment
      export PATH="$${HOME}/bin:$${PATH:-}"
      export PATH="/opt/oracle/instantclient_23_4:/home/opc/bin:$${PATH:-}"      
      export PATH="$${HOME}/venv/bin:$${PATH:-}"
      
    path: //tmp/.nl2sql_env
    permissions: '0644'

runcmd:
  # Ensure packages are installed and updated
  - /usr/bin/dnf update -y
  - /usr/bin/dnf install -y python3.11 python3.11-pip python39-oci-cli unzip curl
  # Not done automatically ... need to do the symlink
  - ln -s /usr/bin/pip3.11 /usr/local/bin/pip
  # oci, unzip and curl  on the command line should work
  
  # Open firewall ports
  - /usr/bin/firewall-cmd --permanent --add-port=8888/tcp
  - /usr/bin/firewall-cmd --permanent --add-port=9000/tcp
  - /usr/bin/firewall-cmd --permanent --add-port=8000/tcp
  - /usr/bin/firewall-cmd --reload
  # sudo firewall-cmd --list-ports
  
  # Set up Python alternatives
  - /usr/sbin/update-alternatives --install /usr/bin/python python /usr/bin/python3.11 40 || echo "Python alternatives setup failed"
  - /usr/sbin/update-alternatives --install /usr/bin/pip pip /usr/bin/pip3.11 40 || echo "Pip alternatives setup failed"        
  # Verify Python installation
  # which python ; python --version ; pip --version

  - which python 
  - python --version 
  - pip --version

  # Install Oracle Instant Client and SQLPlus 23ai
  - /usr/bin/dnf install -y oracle-instantclient-release-el9
  - /usr/bin/dnf -y install oracle-instantclient-release-23ai-el9
  - /usr/bin/dnf install --allowerasing -y oracle-instantclient-sqlplus
  # sqlplus

  # Fix ownership of opc home directory FIRST
  - /bin/chown -R opc:opc /home/opc
  - /bin/chmod 755 /home/opc
  
  # Create the environment file with proper ownership
  - mv /tmp/.nl2sql_env /home/opc/.nl2sql_env
  - /bin/chown opc:opc /home/opc/.nl2sql_env
  
  # Add environment setup to user's bashrc and bash_profile
  - /bin/su - opc -c "echo 'source ~/.nl2sql_env' >> ~/.bashrc"
  - /bin/su - opc -c "echo 'alias ll=\"ls -alF\"' >> ~/.bashrc"
  - /bin/su - opc -c "echo 'alias la=\"ls -A\"' >> ~/.bashrc"
  - /bin/su - opc -c "echo 'alias l=\"ls -CF\"' >> ~/.bashrc"
  - /bin/su - opc -c "echo 'source ~/.nl2sql_env' >> ~/.bash_profile"

  # Set up Python virtual environment with proper user context
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc && python -m ensurepip --upgrade"
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc && python -m pip install --upgrade pip setuptools wheel"
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc && python -m pip install virtualenv"
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc && python -m venv /home/opc/venv"
  - /bin/sudo -u opc -H /bin/bash -c "source /home/opc/venv/bin/activate && pip install --upgrade pip"
  - /bin/sudo -u opc -H /bin/bash -c "source /home/opc/venv/bin/activate && pip install pytest fastapi uvicorn pydantic oracledb oci pandas markdown mkdocs mkdocstrings dotmap requests gunicorn psutil"

  # Download and unzip the application with proper error handling
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc && source ~/.nl2sql_env && oci --auth instance_principal os object get -ns ${namespace} -bn ${deployment_bucket} --name ${zipfile} --file ${zipfile}"
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc && /usr/bin/unzip -o ${zipfile}"
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc && if [ -d nl2sql* ]; then cd nl2sql* && mv * ..; fi"
    
  # Install additional Python dependencies
  - /bin/sudo -u opc -H /bin/bash -c "source /home/opc/venv/bin/activate && pip install asyncio fastapi python-dateutil dotmap requests oci pandas psutil uvicorn oracledb httpx pytest"
  - /bin/sudo -u opc -H /bin/bash -c "cd /home/opc/rest/nl2sql-trust/ && if [ -f requirements.txt ]; then source /home/opc/venv/bin/activate && pip install -r requirements.txt; fi"
  
  # Set proper ownership and permissions AFTER file extraction
  - /bin/chown -R opc:opc /home/opc/
  
  # Make run_app.bash executable and fix any path issues
  - /bin/sudo -u opc -H /bin/bash -c "find /home/opc -name 'run_app.bash' -type f -exec chmod +x {} \;"
  
  # Patch for vm cloud - fix venv path in run_app.bash
  - /bin/sudo -u opc -H /bin/bash -c "if [ -f /home/opc/rest/nl2sql-trust/run_app.bash ]; then sed -i 's|^source /home/app/venv/bin/activate$|source ~/venv/bin/activate|' /home/opc/rest/nl2sql-trust/run_app.bash; fi"
  
  # Debug: Check if the file exists and is executable
  - /bin/sudo -u opc -H /bin/bash -c "ls -la /home/opc/rest/nl2sql-trust/run_app.bash || echo 'run_app.bash not found in expected location'"
  - /bin/sudo -u opc -H /bin/bash -c "find /home/opc -name 'run_app.bash' -type f -ls || echo 'run_app.bash not found anywhere'"
   
  # Enable the service but don't start it yet
  - /usr/bin/systemctl daemon-reload
  - /usr/bin/systemctl enable nl2sql_rest.service
  
  # Wait for all installations to complete
  - /bin/sleep 30
  
  # Final check before starting service
  - /bin/sudo -u opc -H /bin/bash -c "if [ -f /home/opc/rest/nl2sql-trust/run_app.bash ] && [ -x /home/opc/rest/nl2sql-trust/run_app.bash ]; then echo 'run_app.bash is ready'; else echo 'run_app.bash is NOT ready'; fi"
  
  # Start the service
  - /usr/bin/systemctl start nl2sql_rest.service

final_message: |
  NL2SQL instance setup completed!
  
  Installed components:
  - Python 3.11
  - OCI CLI
  - Oracle Instant Client and SQLPlus 23ai
  - NL2SQL application from provided ZIP file
  
  Environment variables set:
  - NL2SQL_OCI_MODE=instance
  - NL2SQL_OCI_BUCKET=${nl2sql_bucket}
  - NL2SQL_OCI_NS=${namespace}
  - NL2SQL_ENV=${nl2sql_env}
  
  Ports opened: 8888, 9000, 8000
  
  The nl2sql_rest.service has been created, enabled, and started.
  
  To check the service status: systemctl status nl2sql_rest.service
  To view logs: journalctl -u nl2sql_rest.service -f
  To restart: systemctl restart nl2sql_rest.service
  
  Note: Please log out and log back in to ensure all environment variables are properly loaded.