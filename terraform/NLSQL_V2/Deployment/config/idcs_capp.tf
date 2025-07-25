locals {
  apex_app_redirect_uri = var.apex_app_redirect_uri
  apex_app_logout_uri = var.apex_app_logout_uri
  oda_base_url = regex("https?://([^/]+).*", module.askdata_oda.oda_instance.web_app_url)[0]
  oda_redirect_rui = "https://${local.oda_base_url}/connectors/v1/callback"
}

module "idcs_confidential_app_apigw" {
    source = "../modules/confidential_apps/apigw"
    region = var.region
    display_name = "${var.object-prefix}-idcs-capp-apigw"
    idcs_endpoint = "${var.idcs_endpoint}:443"
    oda_redirect_uri = [local.oda_redirect_rui]
}

module "idcs_confidential_app_apex"{
  source = "../modules/confidential_apps/apex"
  region = var.region
  display_name = "${var.object-prefix}-idcs-capp-apex"
  idcs_endpoint = "${var.idcs_endpoint}:443"
  apex_app_redirect_uri = local.apex_app_redirect_uri
  apex_app_logout_uri = local.apex_app_logout_uri
}