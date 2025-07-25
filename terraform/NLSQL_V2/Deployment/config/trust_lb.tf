locals {
  trust_lb_display_name = "${var.object-prefix}-trustlb"
  trustlb_backend_set_name = "trustlb-backendset"
  trustlb_backend_set_healthcheck_urlpath = "/ords/"
  trustapp_listener_name = "trustlb-listener"
  trustapp_listener_certificate_id = var.lb_cert_id
  trustapp_lb_hostname = var.lb_hostname
  backend_port = "443"
  lb_healthcheck_port = "443"
  healtcheck_returncode = "302"
}

module "trust_loadbalancer"{
    source = "../modules/load_balancer"
    compartment_id = var.network-compartment-id
    region = var.region
    trust_lb_display_name = local.trust_lb_display_name
    lb_public_subnet = var.public_subnet
    trustlb_backend_set_name = local.trustlb_backend_set_name
    trustlb_backend_set_urlpath = local.trustlb_backend_set_healthcheck_urlpath
    trustapp_instance_ip = module.apex_adw.trust_adw_private_ip
    trustapp_listener_name = local.trustapp_listener_name
    trustapp_listener_certificate_id = local.trustapp_listener_certificate_id
    trustapp_lb_hostname = local.trustapp_lb_hostname
    freeform_tags = var.resource_tags
    backend_port = local.backend_port
    lb_healthcheck_port = local.lb_healthcheck_port
    healtcheck_returncode = local.healtcheck_returncode
}