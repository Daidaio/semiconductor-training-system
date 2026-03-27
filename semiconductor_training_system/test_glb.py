import urllib.request
import urllib.error

try:
    # Test viewer.html
    with urllib.request.urlopen('http://127.0.0.1:8765/viewer.html', timeout=5) as resp:
        print(f'viewer.html Status: {resp.status}')
        print(f'viewer.html Size: {len(resp.read())} bytes')
except Exception as e:
    print(f'viewer.html Error: {e}')

try:
    # Test GLB file  
    req = urllib.request.Request('http://127.0.0.1:8765/asml_duv.glb', method='HEAD')
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(f'GLB Status: {resp.status}')
        content_len = resp.headers.get('Content-Length')
        content_type = resp.headers.get('Content-Type')
        print(f'GLB Content-Length: {content_len}')
        print(f'GLB Content-Type: {content_type}')
except Exception as e:
    print(f'GLB Error: {e}')
