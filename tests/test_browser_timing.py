from http.client import HTTPConnection
from pathlib import Path
import shutil
import subprocess
import threading
from types import SimpleNamespace
import unittest

from g4_lab.server import LabService,create_server


class BrowserTimingTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node unavailable; no installation is performed')
    def test_clock_callback_and_ui_lifecycle_node_contracts(self):
        root=Path(__file__).resolve().parents[1]
        result=subprocess.run([shutil.which('node'),'--test',str(root/'tests/browser_timing.test.cjs')],
                              cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_timing_assets_are_opt_in_and_keep_existing_server_defaults(self):
        for enabled in (False,True):
            service=LabService(SimpleNamespace(sources={'synthetic':{}}))
            server=create_server(service,timing_page=enabled)
            thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=.01),daemon=True);thread.start()
            try:
                for route in ('/','/app.js','/browser-timing.js'):
                    conn=HTTPConnection(*server.server_address,timeout=3)
                    try:
                        conn.request('GET',route);response=conn.getresponse();body=response.read()
                        if route=='/browser-timing.js':self.assertEqual(response.status,200 if enabled else 404)
                        if route=='/':self.assertEqual(b'/browser-timing.js' in body,enabled)
                        if route=='/app.js':self.assertEqual(b'issue_to_first_action_json_response_ms' in body,enabled)
                        self.assertEqual(response.getheader('Cache-Control'),'no-store')
                    finally:conn.close()
            finally:server.shutdown();server.server_close();thread.join(timeout=3)
        with self.assertRaises(ValueError):create_server(None,timing_page=1)


if __name__=='__main__':unittest.main()
