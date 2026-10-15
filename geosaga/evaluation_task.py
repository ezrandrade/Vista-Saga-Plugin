"""Tarefa com entradas imutáveis e processamento GDAL fora da interface Qt."""
from qgis.core import QgsTask
from .raster_engine import run_evaluation


class EvaluationTask(QgsTask):
    def __init__(self, paths, config, destination, report, title, author, callback, report_txt=''):
        super().__init__('Vista Saga — Avaliação', QgsTask.Flag.CanCancel)
        self.paths = list(paths)
        self.config = config
        self.destination = destination
        self.report = report
        self.report_txt = report_txt
        self.title = title
        self.author = author
        self.callback = callback
        self.summary = None
        self.error = ''

    def run(self):
        try:
            self.summary = run_evaluation(
                self.paths, self.config, self.destination, self.report,
                self.title, self.author, progress=self.setProgress,
                cancelled=self.isCanceled, report_txt=self.report_txt,
            )
            return not self.isCanceled()
        except (ValueError, OSError, InterruptedError, RuntimeError) as exc:
            self.error = str(exc)
            return False
        except Exception as exc:
            self.error = f'Falha inesperada ({type(exc).__name__}): {exc}'
            return False

    def finished(self, result):
        if self.callback:
            self.callback(bool(result), self)
        self.callback = None
