"""Rodapé padrão dos módulos (1.4.1, decisão do autor).

[Executar] [Fechar] em todos os módulos, com [Validar] só na Avaliação; sem linha de status, barra de
progresso ou Cancelar fixos no rodapé (progresso e Cancelar numa janela só durante a execução).
"""
import os
import re
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIALOGS = ['signature_dialog.py', 'monitoring_dialog.py', 'vector_monitoring_dialog.py', 'evaluation_dialog.py',
           'vector_evaluation_dialog.py', 'vector_overlay_dialog.py', 'voronoi_dialog.py', 'combination_dialog.py',
           'rs2_dialog.py', 'image_sequence_dialog.py']
OLD_LABELS = ['Calcular assinatura', 'Executar monitoria', 'Executar avaliação', 'Cancelar execução',
              'Executar sobreposição e avaliação', 'Gerar Voronoi', 'Combinar mapas', 'Gerar GIF']


def source(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


class RodapePadrao160(unittest.TestCase):
    def test_sem_rotulos_antigos_do_botao_de_acao(self):
        for name in DIALOGS:
            code = source(name)
            for label in OLD_LABELS:
                self.assertNotIn(f"'{label}'", code, f'{name}: {label}')

    def test_botao_de_acao_executar(self):
        self.assertIn("RUN_TEXT = 'Executar'", source('ui_shared.py'))
        for name in ['signature_dialog.py', 'monitoring_dialog.py', 'vector_monitoring_dialog.py',
                     'voronoi_dialog.py', 'combination_dialog.py', 'image_sequence_dialog.py']:
            self.assertIn('QPushButton(tr(RUN_TEXT))', source(name), name)
        self.assertIn('button(RUN_TEXT, self.execute)', source('evaluation_dialog.py'))
        self.assertIn('RUN_TEXT = STANDARD_RUN_TEXT', source('vector_evaluation_dialog.py'))
        self.assertNotIn('RUN_TEXT =', source('vector_overlay_dialog.py'))   # herda o "Executar"
        self.assertIn("QPushButton(tr('Executar'))", source('rs2_dialog.py'))

    def test_validar_so_na_avaliacao(self):
        for name in DIALOGS:
            has = "'Validar'" in source(name)
            self.assertEqual(has, name in ('evaluation_dialog.py', 'vector_evaluation_dialog.py'), name)

    def test_sem_status_barra_ou_cancelar_fixos(self):
        for name in DIALOGS:
            code = source(name)
            self.assertNotRegex(code, r'self\.status\s*=\s*QLabel', name)
            self.assertNotIn('QProgressBar(', code, name)
            self.assertNotIn('self.cancel_button', code, name)
            self.assertNotRegex(code, r'addWidget\(self\.status', name)
        # O botão de inspeção do Conversor saiu do rodapé, para junto do arquivo de entrada.
        rs2 = source('rs2_dialog.py')
        self.assertIn('source_row.addWidget(self.inspect_button)', rs2)
        self.assertNotIn('actions.addWidget(self.inspect_button)', rs2)

    def test_progresso_em_janela_nas_tarefas(self):
        for name in ('monitoring_dialog.py', 'evaluation_dialog.py'):
            code = source(name)
            self.assertIn('TaskProgressWindow(', code, name)
            self.assertIn('self._progress_window.close()', code, name)

    def test_monitoria_vetorial_executa_pelo_rodape_comum(self):
        code = source('monitoring_dialog.py')
        self.assertIn('self._footer.insertWidget(self._footer.indexOf(self.close_button), dialog.run_button)', code)

    def test_avaliacao_rodape_da_janela_para_as_tres_guias(self):
        code = source('evaluation_dialog.py')
        self.assertIn('root.addLayout(footer)', code)          # fora da guia Raster
        self.assertNotIn('outer.addLayout(footer)', code)
        self.assertIn('self._footer.insertWidget(position, dialog.validate_button)', code)
        self.assertIn('self._footer.insertWidget(position + 1, dialog.run_button)', code)
        self.assertIn('self._update_footer(index)', code)
        self.assertIn('self.validate_button = button(\'Validar\', self.validate_configuration)',
                      source('vector_evaluation_dialog.py'))


class TitulosDasJanelas160(unittest.TestCase):
    """1.4.1-dev2: título do Conversor igual ao menu; janelas de progresso com o título do módulo."""

    def test_titulo_do_conversor(self):
        code = source('rs2_dialog.py')
        self.assertIn("setWindowTitle(tr('Vista Saga Plugin - Conversor de Formatos'))", code)
        self.assertNotIn("'Vista Saga Plugin - Conversor de formatos'", code)

    def test_janelas_de_progresso_com_titulo_do_modulo(self):
        for name in DIALOGS + ['ui_shared.py']:
            lines = source(name).splitlines()
            for i, line in enumerate(lines):
                match = re.match(r'\s*(\w+)\s*=\s*QProgressDialog\(', line)
                if not match:
                    continue
                var = match.group(1)
                window = '\n'.join(lines[i + 1:i + 4])
                self.assertRegex(window, rf'{var}\.setWindowTitle\((self|parent)\.window\(\)\.windowTitle\(\)\)',
                                 f'{name}:{i + 1}')
        for name in DIALOGS:
            self.assertNotRegex(source(name), r"setWindowTitle\(tr\('Vista Saga - ", name)


class FooterStatus160(unittest.TestCase):
    def setUp(self):
        # ui_shared importa tr de geosaga.i18n; carrega o pacote sem QGIS.
        sys.path.insert(0, os.path.dirname(ROOT))

    def test_status_guarda_texto_sem_exibir(self):
        from geosaga.ui_shared import FooterStatus, report_outcome
        status = FooterStatus('Pronto.')
        status.setWordWrap(True)
        status.setVisible(False)
        self.assertEqual(status.text(), 'Pronto.')

        class Bar:
            def __init__(self):
                self.messages = []

            def pushMessage(self, title, text, level=None, duration=None):
                self.messages.append((title, text, duration))

        bar = Bar()
        iface = types.SimpleNamespace(messageBar=lambda: bar)
        report_outcome(status, 'Monitoria', 'Concluída.', 'success', iface)
        self.assertEqual(status.text(), 'Concluída.')
        # Sem QGIS instalado, a barra não é chamada e o texto fica no status (sem exceção).
        try:
            import qgis.core  # noqa: F401
            self.assertEqual(bar.messages[0][1], 'Concluída.')
        except ImportError:
            self.assertEqual(bar.messages, [])


if __name__ == '__main__':
    unittest.main()
