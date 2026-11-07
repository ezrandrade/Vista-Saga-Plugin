import unittest
from pathlib import Path
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

class TaskStabilityTests(unittest.TestCase):
    def test_async_raster_workflow(self):
        content = (ROOT/'voronoi_dialog.py').read_text(encoding='utf-8')
        self.assertIn('class VoronoiRasterTask(QgsTask):', content)
        self.assertIn('QgsApplication.taskManager().addTask(task)', content)
        self.assertIn('self._on_raster_task_finished', content)
        self.assertIn('progress=self.setProgress, cancelled=self.isCanceled', content)
        self.assertIn('task.ui_callback = None', content)
        self.assertIn('Qt.WindowModality.NonModal', content)
        self.assertIn('if not asynchronous:', content)
    def test_shutdown_disconnects(self):
        p=(ROOT/'plugin.py').read_text(encoding='utf-8')
        self.assertIn("getattr(dialog, 'shutdown', None)", p)
        self.assertIn('def shutdown(self):', (ROOT/'voronoi_dialog.py').read_text(encoding='utf-8'))
    def test_version(self):
        _support.assert_release_version(self)

if __name__=='__main__':unittest.main()
