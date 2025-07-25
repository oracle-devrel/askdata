locals {
  lb_access_loggp_name = "trustlb_access_log"
  lb_error_loggp_name = "trustlb_error_log"
}

module "log_groups"{
  source = "../modules/log_groups"
  compartment_id = var.network-compartment-id
  lb_access_loggp_name = local.lb_access_loggp_name
  lb_error_loggp_name = local.lb_error_loggp_name
  freeform_tags = var.resource_tags
}
