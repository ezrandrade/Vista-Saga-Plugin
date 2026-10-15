from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]
def src(fn): return (P/fn).read_text(encoding='utf-8')
class UIModules061(unittest.TestCase):
    def test_raster_vector_tabs(self):
        for f in ('combination_dialog.py', 'evaluation_dialog.py',
                  'monitoring_dialog.py', 'signature_dialog.py'):
            text = src(f)
            self.assertIn('Raster', text, f)
            self.assertIn('vetorial' if f == 'combination_dialog.py' else 'Vetorial', text, f)
    def test_temporary_mode_supported_across_main_modules(self):
        for f in ('combination_dialog.py','evaluation_dialog.py',
                  'vector_evaluation_dialog.py','vector_overlay_dialog.py',
                  'monitoring_dialog.py','vector_monitoring_dialog.py',
                  'signature_dialog.py','rs2_dialog.py'):
            self.assertIn('temporary_destination',src(f),f)
    def test_multi_add_and_remove(self):
        for f in ('combination_dialog.py','evaluation_dialog.py','signature_dialog.py'):
            self.assertIn('choose_project_layers',src(f),f)
        self.assertIn('selectedItems()',src('combination_dialog.py'))
        self.assertIn('selectedItems()',src('signature_dialog.py'))
    def test_rs2_requires_persistent_format(self):
        self.assertIn('operation == 1',src('rs2_dialog.py'))
        self.assertIn('self.temporary_check.setChecked(False)',src('rs2_dialog.py'))
if __name__=='__main__': unittest.main()
