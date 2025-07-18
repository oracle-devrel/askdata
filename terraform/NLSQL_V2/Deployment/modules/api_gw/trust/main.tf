provider "oci" {
  region = var.region
}

resource oci_apigateway_gateway nl2sql_trust_apigw {
  compartment_id = var.compartment_ocid
  display_name  = var.gateway_display_name
  endpoint_type = var.endpoint_type
  freeform_tags = {
  }
  network_security_group_ids = [
  ]
  response_cache_details {
    type = "NONE"
  }
  subnet_id = var.subnet_id
}


resource oci_apigateway_deployment nl2sql-trust-deployment {
  compartment_id = var.compartment_ocid
  display_name = var.deployment_display_name
  freeform_tags = {
  }
  gateway_id  = oci_apigateway_gateway.nl2sql_trust_apigw.id
  path_prefix = var.path_prefix
  specification {
    logging_policies {
      execution_log {
        log_level = "INFO"
      }
    }
    request_policies {
      mutual_tls {
        allowed_sans = [
        ]
        is_verified_certificate_required = "false"
      }
    }
    routes {
      backend {
        connect_timeout_in_seconds = var.connect_timeout_in_seconds
        is_ssl_verify_disabled = "false"
        read_timeout_in_seconds = var.read_timeout_in_seconds
        send_timeout_in_seconds = var.send_timeout_in_seconds
        type = var.backend_type
        url  = var.route1_backend_url
      }
      logging_policies {
        execution_log {
          log_level = "INFO"
        }
      }
      methods = [
        "ANY",
      ]
      path = var.route1_backend_path
    }
  }
}

