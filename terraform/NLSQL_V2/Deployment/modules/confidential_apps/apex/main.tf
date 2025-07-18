provider "oci" {
  region = var.region
}

resource "oci_identity_domains_app" "apex_idcs_confidential_app" {
    based_on_template {
      value = "CustomWebAppTemplateId"
      well_known_id = "CustomWebAppTemplateId"
    }
    display_name = var.display_name
    idcs_endpoint = var.idcs_endpoint
    allow_access_control = true
    active = true
    allowed_grants       = ["authorization_code"]
    client_type         = "confidential"
    is_oauth_client = true
    is_oauth_resource = false
    login_mechanism = "OIDC"
    trust_scope = "Explicit"
    redirect_uris = [var.apex_app_redirect_uri]
    post_logout_redirect_uris = [var.apex_app_logout_uri]
    schemas = [
        "urn:ietf:params:scim:schemas:oracle:idcs:App",
        "urn:ietf:params:scim:schemas:oracle:idcs:extension:OCITags"
    ]
}