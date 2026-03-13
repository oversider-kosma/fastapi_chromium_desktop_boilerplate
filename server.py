import argparse
import threading
import uvicorn
from backend import app
from utils import get_free_port

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
    current_thread = threading.current_thread()
    setattr(current_thread,"server", server)
    server.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--port', type=int)
    args = parser.parse_args()

    port = args.port or get_free_port()
    print(f"Running debug server at 127.0.0.1:{port}...")
    print(f"Press Ctrl-C to quit.")
    try:
        run_server(port)
    except KeyboardInterrupt:
        print()
