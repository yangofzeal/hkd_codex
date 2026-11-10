import io
import tempfile
import unittest
from pathlib import Path
from web_view import handler_for


class Routes(unittest.TestCase):
    def request(self, root, path):
        handler = object.__new__(handler_for(root))
        handler.path = path
        handler.wfile = io.BytesIO()
        handler.send_response = lambda code: setattr(handler, 'code', code)
        handler.send_error = lambda code, *args: setattr(handler, 'code', code)
        handler.send_header = lambda *args: None
        handler.end_headers = lambda: None
        handler.do_GET()
        return handler.code, handler.wfile.getvalue()

    def test_only_explicit_snapshot_routes_are_served(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'index.html').write_text('progress')
            (root / 'status.json').write_text('{}')
            (root / 'secret.txt').write_text('private')
            self.assertEqual(self.request(root, '/'), (200, b'progress'))
            self.assertEqual(self.request(root, '/status.json'), (200, b'{}'))
            for path in ['/secret.txt', '/../secret.txt', '/%2e%2e/secret.txt', '/widgets.json']:
                self.assertEqual(self.request(root, path)[0], 404)
            (root / 'status.json').unlink()
            self.assertEqual(self.request(root, '/status.json')[0], 503)


if __name__ == '__main__':
    unittest.main()
