import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

async def capture():
    user_data = os.path.join(os.environ['TEMP'], 'edge_cdp_profile')
    proc = subprocess.Popen([
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--headless=new",
        f"--user-data-dir={user_data}",
        "--remote-debugging-port=9222",
        "--window-size=1366,1650",
        "http://localhost:8501"
    ])

    try:
        # Wait for debugging port
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://localhost:9222/json/list", timeout=1) as resp:
                    tabs = json.loads(resp.read().decode())
                    for tab in tabs:
                        if tab.get("type") == "page":
                            ws_url = tab["webSocketDebuggerUrl"]
                            break
                    if ws_url:
                        break
            except Exception:
                await asyncio.sleep(0.3)

        if not ws_url:
            print("Failed to get WebSocket debugger URL")
            return

        print(f"Connecting to CDP: {ws_url}")
        async with websockets.connect(ws_url) as ws:
            # Wait for Streamlit to render completely
            await asyncio.sleep(4.0)
            
            # Send capture screenshot command
            cmd = json.dumps({"id": 1, "method": "Page.captureScreenshot", "params": {"format": "png"}})
            await ws.send(cmd)
            resp = await ws.recv()
            data = json.loads(resp)
            img_b64 = data["result"]["data"]
            
            with open("landing_verified.png", "wb") as f:
                f.write(base64.b64decode(img_b64))
            print("Successfully captured full rendered page to landing_verified.png")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(capture())
