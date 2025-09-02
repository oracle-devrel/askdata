# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

"""
Test the API:

    Open your browser and go to:
        http://127.0.0.1:8000/x to test method X().
        http://127.0.0.1:8000/y to test method Y().
        http://127.0.0.1:8000/docs to get the swagger document

    To connect and upload to the vm :
    - ssh connection ssh -i ~/.ssh/<your-private-ssh-key> opc@<your-instance-ip>
    - scp -i ~/.ssh/<your-private-ssh-key> -r ./rest  opc@<your-instance-ip>:~/rest 
    - nohup python np2sql_service.py --mode real --host 0.0.0.0 --port 8000 > np2sql_service.log 2>&1 &
    
"""

import argparse
import logging
#import gunicorn
#from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
#from fastapi.responses import HTMLResponse
#from pathlib import Path
from fastapi.staticfiles import StaticFiles
import uvicorn
import constants
from ui_routers import bootstrap_api, finetune_api, live_certify_api, trust_metrics_api, trust_ops_api, administrative_api,engine_api
from helpers import trust_metrics
from helpers.config_json_helper import config_boostrap

from helpers.database_util import db_create_default_pool
import faulthandler
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
# Create FastAPI app instance
app = FastAPI()
# app.add_middleware(SecurityHeadersMiddleware)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(constants.REST_LAYER)
faulthandler.enable()


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/coverage", StaticFiles(directory="htmlcov", html=True), name="coverage")

app.include_router(bootstrap_api.router, prefix="",  tags=["Bootstrap"])
app.include_router(live_certify_api.router, prefix="", tags=["Live Certify"])
app.include_router(trust_ops_api.router, prefix="", tags=["Trust Operations"])
app.include_router(trust_metrics_api.router, prefix="", tags=["Trust Operations / Trust Metrics"])
app.include_router(finetune_api.router, prefix="")
# app.include_router(engine_api.router, prefix="", tags=["Engine"])
app.include_router(administrative_api.router, prefix="", tags=["Administration"])

@app.get("/health")
async def health_check():
    return {"status": "200"}

@app.get("/favicon.ico")
async def favicon():
    # comes from here: https://www.pinterest.com/pin/48484133475659721/
    # should be replaced. Legal aspect not looked at.
    return FileResponse("static/favicon.ico")


# Optional: Create a redirect from /coverage to /coverage/index.html
@app.get("/cov")
async def coverage_redirect():
    return RedirectResponse(url="/coverage/index.html")

def main():
    """
    Main method for starting the Fast API Application.
    
    | Parameter  | Default |                    Description                           |
    |------------|---------|----------------------------------------------------------|
    | Inst       |  dev    | Installation for now (local, dev, demo)                  |
    | Host       |  real   | IP or FQDN                                               |
    | Port       |  8888   | Port number to listen to                                 |
    | Keepalive  |  300    | Keeping the connection opened for that amount of seconds.|
    | Verbose    |  N/A    | If set, additional traces are output                     |
    | ssl        |  N/A    | If set will start https with self-signed certificate     |

    """

    parser = argparse.ArgumentParser(description=" NLP 2 SQL Rest API")

    parser.add_argument(
        "--inst",
        "-i",
        type=str, 
        nargs="?",  # optional
        default=f"{constants.NL2SQL_MODE_DEFAULT}",  
        help=f"The installation type [{constants.NL2SQL_MODES}]. Default is '{constants.NL2SQL_MODE_DEFAULT}'."
    )
    parser.add_argument(
        "--host",
        "-x",
        type=str, 
        nargs="?",  # optional
        default="127.0.0.1",  # Default IP address (localhost)
        help="The IP address (host). Default is '127.0.0.1'."
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int, 
        nargs="?",  # optional
        default=8000,  # Default port is 8000
        help="The port number. Default is 8000."
    )
    parser.add_argument(
        "--keepalive",
        "-k",
        type=int, 
        nargs="?",  # optional
        default=30,  # Default timeout is 30
        help="The keep alive timeout. Default is 30 minutes."
    )
    parser.add_argument(
         '--verbose',
         '-v',
         action='store_true',
         help='Enable verbose output')

    parser.add_argument(
         '--ssl',
         '-s',
         action='store_true',
         help='Enable ssl')

    args = parser.parse_args()
    
    parser.print_usage()
        
    config_boostrap.setup()
    trust_metrics.set_globals()

    #db_create_default_pool()

    if args.ssl:
        # This is using a self-signed certificate. This is only useful for 
        # limited local development. sblais 22 Nov 2024
        uvicorn.run(app,
                    # threads = 5,
                    workers = 1,
                    host=args.host,
                    port=args.port,
                    timeout_keep_alive=args.keepalive*60,
                    #ssl_keyfile="openssl/private.key",
                    #ssl_certfile="openssl/cert.pem"
                    )
    else:
        uvicorn.run(app,
                    host=args.host,
                    port=args.port,
                    timeout_keep_alive=args.keepalive*60,
                    workers = 1,
                    # threads = 5
        )
    

if __name__ == "__main__":
    main()