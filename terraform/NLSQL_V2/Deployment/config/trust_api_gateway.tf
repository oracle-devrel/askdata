locals {
  gw_endpoint_type = "PUBLIC"
  gw_route_backend_url = "http://${module.trust_python_app.trust_app_instance.private_ip}:8000/$${request.path[endpoints]}"
  gw_route_backend_path = "/{endpoints}"
  trust_gw_display_name = "${var.object-prefix}-trust-apigw"
  gw_deployment_name = "${var.object-prefix}-trust-gwdep"
  gw_path_prefix = "/v1"
  gw_backend_type = "HTTP_BACKEND"
  gw_connect_timeout_in_seconds = 60
  gw_read_timeout_in_seconds = 10
  gw_send_timeout_in_seconds = 10
}

module "trust_api_gw"{
    source = "../modules/api_gw/trust"
    compartment_ocid = var.network-compartment-id
    region = var.region
    subnet_id = var.public_subnet
    route1_backend_path = local.gw_route_backend_path
    route1_backend_url = local.gw_route_backend_url
    gateway_display_name = local.trust_gw_display_name
    deployment_display_name = local.gw_deployment_name
    path_prefix = local.gw_path_prefix
    endpoint_type = local.gw_endpoint_type
    connect_timeout_in_seconds = local.gw_connect_timeout_in_seconds
    read_timeout_in_seconds = local.gw_read_timeout_in_seconds
    send_timeout_in_seconds = local.gw_send_timeout_in_seconds
    backend_type = local.gw_backend_type
    freeform_tags = var.resource_tags
}