# password_generator_api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from password_generation import PasswordGenerator
import threading
import uvicorn

fastapi_app = FastAPI()


class PasswordRequest(BaseModel):
    length: int
    lowercase: bool
    uppercase: bool
    digits: bool
    punctuation: bool


@fastapi_app.post("/generate-password/")
def generate_password(request: PasswordRequest):
    try:
        char_types = []
        if request.lowercase:
            char_types.append('lowercase')
        if request.uppercase:
            char_types.append('uppercase')
        if request.digits:
            char_types.append('digits')
        if request.punctuation:
            char_types.append('punctuation')

        generator = PasswordGenerator(base_length=request.length, char_types=char_types)
        password = generator.password_generator()
        return {"password": password}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ServerThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.server = None

    def run(self):
        config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=self.port)
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


def start_fastapi(port=25698):
    server_thread = ServerThread(port)
    return server_thread


def stop_fastapi(server_thread):
    if server_thread and server_thread.is_alive():
        server_thread.stop()
        server_thread.join()
