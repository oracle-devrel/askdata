provider oci {
	region = var.region
}

resource oci_load_balancer_load_balancer trust_lb {
  compartment_id = var.compartment_id
  display_name = var.trust_lb_display_name
  ip_mode = "IPV4"
  freeform_tags = var.freeform_tags
  is_private            = "false"
  is_request_id_enabled = "true"
  request_id_header = "X-Request-Id"
  shape = "flexible"
  shape_details {
    maximum_bandwidth_in_mbps = "10"
    minimum_bandwidth_in_mbps = "10"
  }
  subnet_ids = [
    var.lb_public_subnet,
  ]
}

resource oci_load_balancer_backend_set trustlb_backend_set {
  health_checker {
    interval_ms = "60000"
    port                = var.lb_healthcheck_port
    protocol            = "HTTP"
    #response_body_regex = ""
    retries             = "3"
    return_code         = var.healtcheck_returncode
    timeout_in_millis   = "3000"
    url_path            = var.trustlb_backend_set_urlpath
  }
  load_balancer_id = oci_load_balancer_load_balancer.trust_lb.id
  name             = var.trustlb_backend_set_name
  policy           = "ROUND_ROBIN"
}

resource oci_load_balancer_backend trustlb_backend {
  backendset_name  = oci_load_balancer_backend_set.trustlb_backend_set.name
  backup           = "false"
  drain            = "false"
  ip_address       = var.trustapp_instance_ip
  load_balancer_id = oci_load_balancer_load_balancer.trust_lb.id
  offline = "false"
  port    = var.backend_port
  weight  = "1"
}

resource oci_load_balancer_listener trustlb_listener {
  connection_configuration {
    backend_tcp_proxy_protocol_options = [
    ]
    backend_tcp_proxy_protocol_version = "0"
    idle_timeout_in_seconds            = "60"
  }
  default_backend_set_name = oci_load_balancer_backend_set.trustlb_backend_set.name
  hostname_names = [
    "trust",
  ]
  load_balancer_id = oci_load_balancer_load_balancer.trust_lb.id
  name             = var.trustapp_listener_name
  port     = "443"
  protocol = "HTTP"
  rule_set_names = [
  ]
  ssl_configuration {
    certificate_ids = [
      var.trustapp_listener_certificate_id,
    ]
    cipher_suite_name      = "oci-wider-compatible-ssl-cipher-suite-v1"
    has_session_resumption = "true"
    protocols = [
      "TLSv1.2",
    ]
    server_order_preference = "ENABLED"
    trusted_certificate_authority_ids = [
    ]
    verify_depth            = "1"
    verify_peer_certificate = "false"
  }
}

resource oci_load_balancer_hostname export_trust {
  hostname         = var.trustapp_lb_hostname
  load_balancer_id = oci_load_balancer_load_balancer.trust_lb.id
  name             = "trust"
}