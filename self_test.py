import subprocess
import time
import httpx
import os
from dotenv import load_dotenv

# Load .env file to get environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def test_backend_connection():
    """Directly tests connection to the backend LLM provider."""
    print("\n--- Testing Backend Connection ---")
    if not OPENAI_BASE_URL:
        print("OPENAI_BASE_URL not set in .env. Skipping backend test.")
        return

    print(f"Attempting to connect to: {OPENAI_BASE_URL}")
    try:
        # A simple GET request to the base URL might not work for all APIs,
        # but it's a good first step to check for network reachability.
        # For OpenAI-compatible APIs, a POST to /chat/completions is better.
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        response = httpx.post(
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers=headers,
            json={
                "model": "test",
                "messages": [{"role": "user", "content": "connection test"}],
                "max_tokens": 1
            },
            timeout=15
        )
        print(f"Backend connection test result: {response.status_code}")
        # We expect an error (e.g., 404 model not found, or 401 bad key), but NOT a timeout.
        if response.status_code:
             print("Backend is reachable.")
    except httpx.TimeoutException:
        print("!!! Backend connection timed out. The server is likely unreachable. !!!")
    except httpx.RequestError as e:
        print(f"!!! Backend connection failed: {e} !!!")


def run_test():
    """
    Automated test for the proxy server.
    1. Starts the server.
    2. Waits for it to be ready.
    3. Sends a test request.
    4. Prints server logs and test result.
    5. Stops the server.
    """
    server_process = None
    try:
        # 1. Start the server
        print("--- Starting server ---")
        server_process = subprocess.Popen(
            ["python", "start_proxy.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # 2. Wait for the server to be ready
        print("--- Waiting for server to start (max 10s) ---")
        start_time = time.time()
        server_ready = False
        while time.time() - start_time < 10:
            if server_process.stdout:
                line = server_process.stdout.readline()
                print(f"SERVER: {line.strip()}")
                if "Uvicorn running on" in line:
                    server_ready = True
                    break
            time.sleep(0.1)

        if not server_ready:
            print("!!! Server failed to start in time. Aborting. !!!")
            return

        # 3. Send a test request
        print("\n--- Sending test request ---")
        headers = {}
        if ANTHROPIC_API_KEY:
            headers["Authorization"] = f"Bearer {ANTHROPIC_API_KEY}"
            print(f"Using API Key: {ANTHROPIC_API_KEY}")
        else:
            print("No ANTHROPIC_API_KEY found in .env, sending request without auth.")

        try:
            response = httpx.post(
                "http://localhost:8082/v1/messages",
                headers=headers,
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "self-test"}],
                },
                timeout=10,
            )
            print("\n--- Test Result ---")
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
        except httpx.RequestError as e:
            print("\n--- Test Result ---")
            print(f"!!! Request failed: {e} !!!")

    finally:
        # 5. Stop the server
        if server_process:
            print("\n--- Stopping server ---")
            server_process.terminate()
            try:
                # Wait for the process to terminate and read remaining output
                stdout, _ = server_process.communicate(timeout=5)
                print("--- Remaining Server Output ---")
                for line in stdout.splitlines():
                    print(f"SERVER: {line.strip()}")
            except subprocess.TimeoutExpired:
                print("Server did not terminate gracefully, killing.")
                server_process.kill()
            print("--- Server stopped ---")

if __name__ == "__main__":
    test_backend_connection()
    run_test()