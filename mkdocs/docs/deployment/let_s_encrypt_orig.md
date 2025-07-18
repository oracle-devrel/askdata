# Let's Encrypt Certificate Generation (Original)

Let's Encrypt can be used to generate SSL certificates. Here is a simple method to do this based on: <br>
<https://www.ateam-oracle.com/post/get-certificates-from-lets-encrypt-for-your-oci-services-the-easy-way>

# High-level Process

This uses the certbot tool from Let's encrypt

1.  certbot certonly –logs-dir logs --work-dir work --config-dir config --authenticator dns-oci -d _load balancer FQDN_

2.  Upload to the certificate manager

| File | Location |
|------|----------|
|cert.pem@  | _base_/config/archive/_load balancer FQDN_/cert1.pem |
|fullchain.pem@ | _base_/config/archive/_load balancer FQDN_/fullchain1.pem |
|privkey.pem@  | _base_/config/archive/_load balancer FQDN_/privkey1.pem |

# Dependency List

1. A machine with Python installed.
2.  This requires an internet domain
    1.  nip.io or sslip.io can be used. (doesn't look good for demos)
3.  oci cli is installed and has access to the DNS
4.  Install certbot on a linux server
    1.  pip install certbot
    2.  pip install certbot-dns-oci

# Network Configuration

N/A

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
