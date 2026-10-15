"""Execução da Monitoria em QgsTask, isolada de widgets e camadas Qt."""
from qgis.core import QgsTask

from .monitoring_engine import run_monitoring


class MonitoringTask(QgsTask):
    def __init__(self, before, after, output, before_label, after_label, title, callback,
                 descriptive_legend=True, temporal_files=None, legend_lookup=''):
        super().__init__('Vista Saga — Monitoria', QgsTask.Flag.CanCancel)
        self.before = before
        self.after = after
        self.output = output
        self.before_label = before_label
        self.after_label = after_label
        self.title = title
        self.callback = callback
        self.descriptive_legend = bool(descriptive_legend)
        self.temporal_files = list(temporal_files or [])
        self.legend_lookup = legend_lookup
        self.result = None
        self.error = ''

    def run(self):
        try:
            self.result = run_monitoring(
                self.before, self.after, self.output,
                before_label=self.before_label, after_label=self.after_label,
                title=self.title, progress=self.setProgress, cancelled=self.isCanceled,
                descriptive_legend=self.descriptive_legend, temporal_files=self.temporal_files,
                legend_lookup=self.legend_lookup,
            )
            return not self.isCanceled()
        except (OSError, RuntimeError, ValueError, InterruptedError) as exc:
            self.error = str(exc)
            return False
        except Exception as exc:
            self.error = f'Falha inesperada ({type(exc).__name__}): {exc}'
            return False

    def finished(self, success):
        if self.callback is not None:
            self.callback(bool(success), self)
        self.callback = None
