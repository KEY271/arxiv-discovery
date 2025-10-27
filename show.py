from jinja2 import Environment, FileSystemLoader, select_autoescape
import json5
import http.server
import socketserver
import webbrowser
import threading
import time
import sys
import os

def load_settings() -> dict:
    if not os.path.exists("settings.json5"):
        raise FileNotFoundError("settings.json5 not found. Copy settings.example.json5 to settings.json5 and configure it.")
    with open("settings.json5", "r") as f:
        config = json5.load(f)
    return config

def undump(value):
    if isinstance(value, str):
        try:
            return json5.loads(value)
        except Exception:
            return value
    return value

def trusted(config):
    trusted_authors = set(config.get("trusted_authors", []))
    def trusted_filter(value):
        if value in trusted_authors:
            return f"<span class='trusted'>{value}</span>"
        return f"<span>{value}</span>"
    return trusted_filter

def render_results(config):
    with open("out/results.json5", "r", encoding="utf-8") as f:
        results = json5.load(f)
    env = Environment(loader=FileSystemLoader('.'), autoescape=select_autoescape(["html", "xml"]))
    env.filters["undump"] = undump
    env.filters["trusted"] = trusted(config)
    template = env.get_template("template.html.j2")
    data = {
        "fetched_at": results["fetched_at"],
        "papers": results["papers"]
    }
    output = template.render(data)
    with open("out/index.html", "w", encoding="utf-8") as f:
        f.write(output)

def main():
    config = load_settings()
    render_results(config)
    PORT = 8009
    Handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", PORT), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print(f"Serving at http://localhost:{PORT}/out")
    webbrowser.open(f"http://localhost:{PORT}/out")
    try:
        while(True):
            time.sleep(10000)
    except KeyboardInterrupt:
        print("closing.")
        server.socket.close()
        sys.exit()

if __name__ == "__main__":
    main()
