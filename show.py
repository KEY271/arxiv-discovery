from jinja2 import Environment, FileSystemLoader, select_autoescape
import json5
import http.server
import socketserver
import webbrowser
import threading
import time
import sys

def undump(value):
    if isinstance(value, str):
        try:
            return json5.loads(value)
        except Exception:
            return value
    return value

def render_results():
    with open("results.json5", "r", encoding="utf-8") as f:
        results = json5.load(f)
    env = Environment(loader=FileSystemLoader('.'), autoescape=select_autoescape(["html", "xml"]))
    env.filters["undump"] = undump
    template = env.get_template("template.html.j2")
    data = {
        "papers": results
    }
    output = template.render(data)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(output)

def main():
    render_results()
    PORT = 8009
    Handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", PORT), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print(f"Serving at http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        while(True):
            time.sleep(10000)
    except KeyboardInterrupt:
        print("closing.")
        server.socket.close()
        sys.exit()

if __name__ == "__main__":
    main()
