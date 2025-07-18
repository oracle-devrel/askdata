# Let's Encrypt Certificate Generation

<p>This is an update on the let's encrypt original page.</p>

The newer version of cerbot don't work with the oci-dns. Because of this, we need to fix the actual versions being used until it is fixed and works again. This is unlikely as oci-dns doesn't seem to be actively supported. Note that if you're using ports 80 or 443, then oci-dns may not be required.

# High-level Process

This uses the certbot tool from Let's encrypt

1.  certbot certonly --authenticator dns-oci --dns-oci-propagation-seconds 60 --logs-dir logs --work-dir work --config-dir config --key-type ecdsa --elliptic-curve secp256r1 -d _load balancer FQDN_

2.  Upload to the certificate manager

| File | Location |
|------|----------|
|cert.pem@  | _base_/config/live/_load balancer FQDN_/cert1.pem |
|fullchain.pem@ | _base_/config/live/_load balancer FQDN_/fullchain1.pem |
|privkey.pem@  | _base_/config/live/_load balancer FQDN_/privkey1.pem |

# Dependency List

1. python 3.11 installed
2. oci cli and sdk installed

``` requirement.txt
certbot==1.14.0
acme==1.14.0
pyOpenSSL==22.0.0
cryptography==36.0.2
certbot-dns-oci==0.3.6
oci==2.104.2
josepy==1.3.0
```

``` bash
# Cleaning up steps if required
deactivate
rm -rf ~/venvs/certbot-env311/
python3.11 -m venv ~/venvs/certbot-env311

# move into the venv
source ~/venvs/certbot-env311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
find ~/venvs/certbot-env311/lib/python3.11/site-packages -name "*.pyc" -delete
```

``` bash
# To generate the cert
certbot certonly --authenticator dns-oci --dns-oci-propagation-seconds 60 --logs-dir logs --work-dir work --config-dir config --key-type ecdsa --elliptic-curve secp256r1 -d _load balancer FQDN_
```
# For Certificate rotation (not tested)
``` bash
# Create a new version of an existing certificate
oci certs-mgmt certificate-version create-by-importing-config \
  --certificate-id <existing-certificate-ocid> \
  --certificate-pem file:///<path>/live/trust.nl2sql.dev/fullchain.pem \
  --private-key-pem file:///<path>/live/trust.nl2sql.dev/privkey.pem \
  --certificate-chain-pem file:///<path>/live/trust.nl2sql.dev/chain.pem \
  --version-name "v$(date +%Y%m%d)"
```

# Configuration Steps

| **Name** | **Description** | **Automation** |
|----|----|----|
| installation | Install certbot and certbot-dns-oci | Python setup |
| Installation | install the oracle oci cli | Python setup |
| creation | Create the SSL Certificate | certbot call |
| publish | Import the cert, fullchain and privkey to the certificate manager. | oci script |

# Validation

you can use open ssl

openssl x509 -in \<certificate_file\> -noout -enddate
