locals {
  instance_dynamic_group_rule = "Any {instance.id = '${module.nlsql_engine_app.nlsql_engine_instance.id}', instance.id = '${module.trust_python_app.trust_app_instance.id}'}"
  api_gw_dynamic_group_rule = "ANY {resource.type = 'ApiGateway', resource.id = '${module.business_api_gw.api_gateway.id}', resource.compartment.id = '${var.network-compartment-id}'}"
}

module "instance_principals" {
  source = "./../modules/iam_dynamic_group/"
  region = var.region
  tenancy_ocid = var.tenancy_ocid
  dynamic_group_name = "${var.object-prefix}-instance-principal-dg"
  instance_dynamic_group_rule = local.instance_dynamic_group_rule
  api_gw_dynamic_group_rule = local.api_gw_dynamic_group_rule
}

module "instance_principal_policy"{
  source = "./../modules/iam_policy/"
  region = var.region
  tenancy_ocid = var.tenancy_ocid
  policy_name = "${var.object-prefix}-nl2sql-iam-policy"
  instance_principal_dg_id = module.instance_principals.instance_principal_dg.id
  business_apigw_dg_id = module.instance_principals.business_apigw_dg.id
  security_compartment = var.security-compartment-id
  appdev_compartment = var.app-compartment-id
  database_compartment = var.database-compartment-id
}

