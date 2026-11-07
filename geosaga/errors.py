"""Registro de falhas inesperadas no painel de mensagens do QGIS.

Exceções capturadas por ``except Exception`` não podem desaparecer: o
traceback completo vai para a aba "Vista Saga Plugin" do painel de mensagens
(Exibir → Painéis → Mensagens de log), e o usuário vê uma mensagem curta.
``QgsMessageLog`` é seguro para chamadas a partir de threads de QgsTask.
"""
import traceback

LOG_TAG = 'Vista Saga Plugin'


def log_exception(context=''):
    """Registra o traceback da exceção em tratamento; nunca lança exceção."""
    try:
        from qgis.core import Qgis, QgsMessageLog
        text = traceback.format_exc()
        if context:
            text = f'{context}\n{text}'
        QgsMessageLog.logMessage(text, LOG_TAG, Qgis.MessageLevel.Critical)
    except Exception:  # o registro de falhas jamais pode gerar nova falha
        pass


def log_warning(message):
    try:
        from qgis.core import Qgis, QgsMessageLog
        QgsMessageLog.logMessage(str(message), LOG_TAG, Qgis.MessageLevel.Warning)
    except Exception:  # idem
        pass
