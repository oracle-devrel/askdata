import requests
import base64
import json
from config import config, logger

# https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/OATOAuthClientWebApp.htm
# https://docs.oracle.com/en/cloud/paas/iam-domains-rest-api/op-admin-v1-apps-id-get.html
def validate_token(token):

    try:
        domain_url = config["identity_domain"]["domain_url"]
        app_id = config["identity_domain"]["app_id"]

        # Attempt to make a GET request to a protected endpoint
        response = requests.get(
            f"https://{domain_url}.identity.oraclecloud.com/admin/v1/Apps/{app_id}", # TODO: The oauth2 introspect api may be better endpoint to check, but giving me errors when trying it: https://docs.oracle.com/en/cloud/paas/iam-domains-rest-api/op-oauth2-v1-introspect-post.html
            headers={"Authorization": f"Bearer {token}","Content-Type":"application/scim+json"},
        )
        logger.info(response.status_code)
        logger.debug(vars(response))
        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Client authorized") # TODO: any identifying info to print about client in headers?
            return True
        else:
            logger.info("Unauthorized credentials")
            logger.debug(vars(response))
            return False
    except Exception as e:
        logger.error(f"An error occurred while validating the Bearer token: {e}")
        return False

# https://docs.oracle.com/en/cloud/paas/iam-domains-rest-api/op-oauth2-v1-token-post.html
def create_token():
    try:
        domain_url = config["identity_domain"]["domain_url"]
        client_id = config["identity_domain"]["client_id"]
        client_secret = config["identity_domain"]["client_secret"]

        encoded_credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        logger.debug(encoded_credentials)
        response = requests.post(
            f"https://{domain_url}.identity.oraclecloud.com/oauth2/v1/token",
            headers={"Authorization": f"Basic {encoded_credentials}", "Content-Type":"application/x-www-form-urlencoded"},
            data={'grant_type': 'client_credentials','scope': 'urn:opc:idm:__myscopes__'}
        )
        logger.debug(vars(response.request))
        logger.debug(vars(response))
        if response.status_code == 200:
            return json.loads(response.content.decode())["access_token"]
        else:
            logger.error("Error creating Bearer token")
            return "error"

    except Exception as e:
        logger.error(f"An error occurred while creating the Bearer token: {e}")


def test_token():

    enabled = config["identity_domain"]["enabled"]

    logger.info(f"Token authentication: {enabled}")
    if not enabled:
        return

    try:
        token = create_token()
        logger.debug("token created successfully")
    except Exception as e:
        logger.error(f"error creating token: {e}")
        return
    try:
        logger.info( f"Token Valid?: {validate_token(token)}")
    except Exception as e:
        logger.error(f"error validating token: {e}")

