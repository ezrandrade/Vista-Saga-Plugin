import tempfile
import unittest
from pathlib import Path
from geosaga.gif_codec import encode_gif
from PIL import Image

class GifCodecTest(unittest.TestCase):
    def test_two_frame_exact_colors_and_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'demo.gif'
            red=bytes((255,0,0))*256
            blue=bytes((0,0,255))*256
            result=encode_gif(target,[red,blue],16,16,delay_cs=75)
            self.assertFalse(result['palette_quantized'])
            with Image.open(target) as im:
                self.assertEqual(im.n_frames,2)
                self.assertEqual(im.size,(16,16))
                self.assertEqual(im.info['duration'],750)
                self.assertEqual(im.convert('RGB').getpixel((0,0)),(255,0,0))
                im.seek(1)
                self.assertEqual(im.convert('RGB').getpixel((0,0)),(0,0,255))
    def test_256_unique_colors_and_lzw_code_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'matrix.gif'
            frame=bytes(n for n in range(256) for _ in range(3)) * 40
            res=encode_gif(target,[frame],256,40)
            with Image.open(target) as source:
                im=source.convert('RGB')
                self.assertEqual(im.getpixel((0,0)),(0,0,0))
                self.assertEqual(im.getpixel((255,39)),(255,255,255))
    def test_invalid_dimensions_do_not_create_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'bad.gif'
            with self.assertRaisesRegex(ValueError,'dimensões'):
                encode_gif(target,[b'123'],2,2)
            self.assertFalse(target.exists())
    def test_more_than_256_colors_is_quantized(self):
        with tempfile.TemporaryDirectory() as directory:
            rgb=bytearray()
            for i in range(300): rgb.extend((i%256,i//256,128))
            result=encode_gif(Path(directory)/'q.gif',[rgb],30,10)
            self.assertTrue(result['palette_quantized'])
            with Image.open(result['path']) as im:
                self.assertEqual(im.size,(30,10))
if __name__=='__main__': unittest.main()
