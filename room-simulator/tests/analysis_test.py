"""Real-model API smoke checks. Run from room-simulator with the analysis venv."""
import io
from pathlib import Path
import unittest

from fastapi.testclient import TestClient
from PIL import Image
from analysis.server import app


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_real_photo_detection_and_finite_relative_depth(self):
        path = Path(__file__).resolve().parents[2] / 'images' / '2.jpg'
        image = Image.open(path).convert('RGB')
        image.thumbnail((768, 768))
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        response = self.client.post('/api/analyze', files={'image': ('photo.jpg', buffer.getvalue(), 'image/jpeg')})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual((data['width'], data['height']), image.size)
        self.assertTrue(any(obj['label'] == 'chair' for obj in data['objects']))
        depth = data['depth']
        self.assertEqual(len(depth['values']), depth['width'] * depth['height'])
        self.assertTrue(all(0 <= p <= 1 for p in depth['values']))
        self.assertGreater(max(depth['values']) - min(depth['values']), .9)
        self.assertNotIn('meters', data)

    def test_invalid_upload_rejected(self):
        response = self.client.post('/api/analyze', files={'image': ('bad.jpg', b'not an image', 'image/jpeg')})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get('/api/health').json()['metric_depth'], False)

    def test_tiny_image_rejected(self):
        buffer = io.BytesIO()
        Image.new('RGB', (8, 8)).save(buffer, format='PNG')
        response = self.client.post('/api/analyze', files={'image': ('tiny.png', buffer.getvalue(), 'image/png')})
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
