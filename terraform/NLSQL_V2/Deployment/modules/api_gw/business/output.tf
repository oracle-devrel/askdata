output "apigw_deployment" {
  value = oci_apigateway_deployment.askdata_apigw_deployment
}

output "api_gateway"{
    value = oci_apigateway_gateway.askdata_apigw
}