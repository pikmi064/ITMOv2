"""Independent probe: UTF-8 contract must not silently accept UTF-16/32."""
import http.client
import json
import select
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='reviewer-encoding-') as temporary:
    process = subprocess.Popen([sys.executable, str(root/'project/server.py'), '--port', '0', '--database', str(Path(temporary)/'tasks.sqlite3')], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        assert select.select([process.stdout], [], [], 5)[0]
        port = int(process.stdout.readline().strip().rsplit(':',1)[1])
        def call(method, endpoint, raw=None):
            client=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
            try:
                client.request(method, endpoint, raw, {'Content-Type':'application/json; charset=utf-8'})
                response=client.getresponse()
                return response.status,json.loads(response.read())
            finally: client.close()
        _,created=call('POST','/api/tasks',b'{"title":"Original"}')
        for encoding in ('utf-16','utf-32'):
            before=call('GET','/api/tasks')[1]
            raw=json.dumps({'title':'Unexpected '+encoding,'subject':'','deadline':''}).encode(encoding)
            status,body=call('PUT',f"/api/tasks/{created['id']}",raw)
            after=call('GET','/api/tasks')[1]
            print(json.dumps({'encoding':encoding,'expected_status':400,'expected_unchanged':True,'actual_status':status,'actual_unchanged':before==after,'response':body},ensure_ascii=False))
    finally:
        process.terminate();process.wait(timeout=5)
