from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from contextlib import asynccontextmanager
from typing import List
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


from config import config, logger
from identity_domain_auth import validate_token, test_token
from cache import cache


cache_obj = cache()



# Store connected WebSocket clients (for example, to handle multiple clients if needed)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket, code=1000):
        await websocket.close(code) # TODO: websocket is not sending disconnect message to the client
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

app = FastAPI()


app.config = config

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint for handling suggestions
@app.websocket("/wss/suggestions")
async def websocket_endpoint(websocket: WebSocket,token: str = Query("")):
    await manager.connect(websocket)

    if app.config["identity_domain"]["enabled"]:
        try:
            if validate_token(token):
                1
            #headers = dict(websocket.headers)
            #if validate_token(headers["authorization"]):
                #1
            else:
                await manager.disconnect(websocket,code = 1008)
                return
        except Exception as e:
            logger.error(f"Error Authenticating client: {e}")
            await manager.disconnect(websocket,code = 1008)
            return

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            # Assume we are getting a JSON object with a query field
            query = data  # Process the data as needed, e.g., extract text
            # Generate suggestions based on the query
            # Here, mock suggestions are provided; replace with actual logic
            suggestions = cache_obj.semantic_search(query, 5)
            results = cache_obj.process_results([item[0] for item in suggestions]);
            logger.debug("*****debug4****")
            logger.info(f"suggestions: {suggestions}")
            logger.debug("*****debug5****")
            #suggestions = ["Suggestion 1", "Suggestion 2", "Suggestion 3"]  # Example suggestions
            #await websocket.send_json({"action": "suggestions", "similar_prompts": suggestions})
            await websocket.send_json({"message" : results})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)



# Entry point to run the app with uvicorn
if __name__ == "__main__":
    test_token()

    port = config["websocket"]["port"]

    if config["ssl"]["enabled"]:
        uvicorn.run("semantic_suggest:app", host="0.0.0.0", port=port, ssl_certfile=config["ssl"]["ssl_certfile"], ssl_keyfile=config["ssl"]["ssl_keyfile"], reload=True)
    else:
        uvicorn.run("semantic_suggest:app", host="0.0.0.0", port=port, reload=True)

