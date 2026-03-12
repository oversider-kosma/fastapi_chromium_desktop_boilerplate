import threading
import uvicorn
from backend import app

class AppServer(uvicorn.Server):
    def install_setup(self) -> None:
        # Redefine to prevent uvicorn from intercepting Ctrl+C
        pass

def run_server(port) -> None:
    uvi_config = uvicorn.Config(
        app=app, 
        host='127.0.0.1', 
        port=port, 
        log_level="info",
        loop="asyncio"
    )
    server = AppServer(config=uvi_config)
    
    # Save the server link in the thread attribute
    threading.current_thread().server = server
    server.run()
