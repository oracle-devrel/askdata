# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import dotmap


ctrl = {
    "control":
        {"config":None,
            "test":{
                "mode": True, # Need to test absent or False
                "out_of_scope":{
                        "database": ["insert","update"]
                        }
                }
        }
    }

control = dotmap.DotMap(ctrl["control"])

if control.test.mode:
    print("in test mode")

if control.test.mode and "update" in  control.test.out_of_scope.database:
    print("in test mode and update out of scope")

if control.something:
    print("shouldn't be here.")