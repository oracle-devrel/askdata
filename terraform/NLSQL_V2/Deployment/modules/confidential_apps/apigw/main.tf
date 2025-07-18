provider "oci" {
  region = var.region
}

resource "oci_identity_domains_app" "apigw_idcs_confidential_app" {
    based_on_template {
      value = "CustomWebAppTemplateId"
      well_known_id = "CustomWebAppTemplateId"
    }
    display_name = var.display_name
    idcs_endpoint = var.idcs_endpoint
    access_token_expiry = 3600
    allow_access_control = true
    active = true
    allowed_grants       = ["password",
                            "client_credentials",
                            "urn:ietf:params:oauth:grant-type:jwt-bearer",
                            "urn:ietf:params:oauth:grant-type:saml2-bearer",
                            "tls_client_auth",
                            "refresh_token",
                            "urn:ietf:params:oauth:grant-type:device_code",
                            "authorization_code",
                            "implicit"]
    client_type         = "confidential"
    bypass_consent = true
    is_oauth_client = true
    is_oauth_resource = false
    login_mechanism = "OIDC"
    redirect_uris = var.oda_redirect_uri
    trust_scope = "Explicit"
    schemas = [
        "urn:ietf:params:scim:schemas:oracle:idcs:App",
        "urn:ietf:params:scim:schemas:oracle:idcs:extension:OCITags"
    ]
}