# Use Oracle Linux 8 as the base image
# oci os 

#RELEASE_FILE=release.zip - This is from the object store read
#RELEASE_NAME=nl2sql-2025W15 - This is the name of the top directory in the release file.
# cd /nl2sql
# docker build --progress=plain -f rest/script/docker/Dockerfile -t nl2sql-trust .
# or clear; docker build --no-cache  -t  nl2sql-trust .
# The first port is the external port so, external:internal
# docker run -d -p 9000:8000 -p 9888:8888 --name nl2sql-trust trust-nl2sql-2025w15
# docker run -it -p 9000:8000 -p 9888:8888 --name nl2sql-trust trust-nl2sql-2025w15 /bin/bash
# docker exec -it nl2sql-trust /bin/bash
# docker logs --tail 1000 nl2sql-trust -f
# docker container prune -f ; docker volume prune -f ; docker builder prune --all -f ; docker system df

FROM oraclelinux:8

# Set environment variables for non-interactive installation
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

ENV NL2SQL_HOST=0.0.0.0
ENV NL2SQL_PORT=8000
# Expose the necessary ports
EXPOSE 8000 8888

# Install dependencies for the application and Python packages
RUN yum -y update && yum -y groupinstall "Development Tools"

RUN yum -y install \
    unzip \
    python3 \
    python3-pip \
    python3-devel

    RUN yum -y install \
    wget \
    gcc \
    make \
    git \
    sudo \
    libaio \
    gdb

RUN dnf install -y epel-release

#   This repository doesn't seems to be available in the linux image. So this is a copy of what
#we have on the cloud VM.
COPY rest/script/docker/oracle-instantclient-23ai-ol8.repo /etc/yum.repos.d/oracle-instantclient-23ai-ol8.repo

RUN yum -y install oracle-release-el8 && \
    yum -y install oracle-instantclient-sqlplus* && \
    yum -y install oracle-instantclient-tools* 
RUN  yum clean all

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN echo "1" | update-alternatives --config python3

# Verify Python version
RUN python3 --version

COPY rest/nl2sql-trust /home/app/rest/nl2sql-trust

#-----------------------
#    Set the app user
#-----------------------
RUN groupadd sudo

RUN useradd -m -s /bin/bash app && \
    echo "app:app" | chpasswd && \
    usermod -aG sudo app
#RUN echo "%sudo   ALL=(ALL:ALL) ALL" >> /etc/sudoers
RUN echo 'app ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN chown app:app /home/app

RUN curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh | \
        bash -s -- --accept-all-defaults --exec-dir /usr/local/bin --install-dir /usr/local/lib/oci-cli

# Switch to the 'app' user
USER app
WORKDIR /home/app

COPY --chown=app:app rest/script/docker/oci /home/app/.oci
COPY --chown=app:app mkdocs /home/app/mkdocs

#-------------------------------
#    Set the virtual environment
#-------------------------------
# Ensure pip and setuptools are upgraded correctly
RUN python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install virtualenv && \
    python3 -m venv /home/app/venv

ENV PATH="~/venv/bin:$PATH"

# Install required dependencies
RUN source /home/app/venv/bin/activate && \
    pip install --upgrade pip && \
    pip install pytest fastapi uvicorn pydantic oracledb oci pandas markdown mkdocs mkdocstrings dotmap requests gunicorn psutil

##--------------------------------------------------------------------------------
#    Set the application
##--------------------------------------------------------------------------------

# Transfer supporting files in the container
COPY rest/script/docker/init_trust.bash /home/app/init_trust.bash
COPY rest/script/docker/run_app.bash /home/app/run_app.bash
RUN ls -lasrt /home/app

# Overwrite the sqlnet and ojdbc so it has the TNS_ADMIN in it.
USER app
COPY rest/script/docker/init_trust.bash /home/app/rest/nl2sql-trust/init_trust.bash
COPY rest/script/docker/run_app.bash /home/app/rest/nl2sql-trust/run_app.bash

USER root
RUN chown app:app /home/app/rest/nl2sql-trust/init_trust.bash
RUN chown app:app /home/app/rest/nl2sql-trust/run_app.bash
RUN chmod +x /home/app/rest/nl2sql-trust/init_trust.bash
RUN chmod +x /home/app/rest/nl2sql-trust/run_app.bash

# Make the init_trust.bash script executable and run it for customization
# For now, it doesn't do anything.
USER app
# RUN /home/app/rest/nl2sql-trust/init_trust.bash

# Command to start the service
# python3 /home/app/rest/nl2sql-trust/nl2sql_service.py --inst dev --host 0.0.0.0 --port 8000
CMD ["/bin/bash", "/home/app/rest/nl2sql-trust/run_app.bash"]
