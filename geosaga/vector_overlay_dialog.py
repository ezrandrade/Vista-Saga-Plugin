"""Interface de Avaliação por sobreposição de VÁRIAS camadas vetoriais.

Aproveita as mesmas tabelas de notas e pesos já homologadas na avaliação de
atributos; apenas altera a fonte de cada critério e o processamento geométrico.
"""
from .i18n import tr
import os
from collections import Counter

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QFileDialog, QGroupBox, QMessageBox,
    QProgressDialog, QPushButton,
)
from qgis.core import QgsProject

from .vector_evaluation_core import category_key
from .vector_evaluation_dialog import VectorEvaluationDialog
from .ui_shared import choose_project_layers, temporary_destination
from .vector_overlay_engine import validate_overlay_plan, validate_source_layers, evaluate_overlay


class VectorOverlayEvaluationDialog(VectorEvaluationDialog):
    def _build(self):
        super()._build()
        self.setWindowTitle(tr('Vista Saga Plugin — Avaliação por sobreposição'))
        self.setMinimumSize(900, 625)
        heading = self.layout().itemAt(0).widget()
        heading.setText(tr('<b>AVALIAÇÃO ESPACIAL — SOBREPOSIÇÃO DE MAPAS VETORIAIS</b>'))
        self.layout().itemAt(1).widget().setText(
            tr('Adicione pelo menos duas camadas poligonais do QGIS, escolhendo um campo temático '
            'para cada mapa. Defina pesos e notas por classe. O plugin cruzará as geometrias '
            'e avaliará somente as regiões comuns a todas as camadas (interseção espacial). '
            'Os originais não serão modificados.'))
        for group in self.findChildren(QGroupBox):
            if group.title().startswith('1.'):
                group.setTitle(tr('1. Selecionar próximo mapa vetorial'))
            elif group.title().startswith('2.'):
                group.setTitle(tr('2. Camadas empilhadas e pesos'))
            elif group.title().startswith('3.'):
                group.setTitle(tr('3. Categorias, notas e exclusões'))
        for control in self.findChildren(QPushButton):
            if control.text() == 'Empilhar camadas vetoriais independentes…':
                control.hide()
            if control.text() == 'Adicionar campo':
                control.setText(tr('Adicionar camada'))
            elif control.text() == 'Remover campo selecionado':
                control.setText(tr('Remover camada selecionada'))
        self.criteria_table.setHorizontalHeaderLabels([tr('Mapa / campo'), tr('Peso (%)'), tr('Categorias')])
        self.class_label.setText(tr('Adicione um mapa e selecione-o na lista.'))
        self.status.setText(tr('Adicione duas ou mais camadas com SRC igual e área comum.'))
        self.output_edit.setPlaceholderText(tr('Salvar polígonos avaliados por sobreposição (.gpkg)'))
        button_bulk = QPushButton(tr('Adicionar várias camadas do QGIS…'))
        button_bulk.clicked.connect(self.add_project_many)
        self.layout().insertWidget(3, button_bulk)
        self.run_button.setText(tr('Executar sobreposição e avaliação'))

    def _layer_changed(self, _layer=None):
        # Diferentemente da avaliação por atributos, TROCAR a camada no seletor
        # não deve apagar a pilha configurada anteriormente.
        if not self.running and hasattr(self, 'field_combo'):
            self._populate_fields()

    def add_project_many(self):
        from qgis.PyQt.QtWidgets import QInputDialog
        for layer in choose_project_layers(self, 'vector', 'Empilhar mapas vetoriais'):
            if any(c['layer_id'] == layer.id() for c in self.criteria):
                continue
            if not layer.isValid() or not layer.fields().names():
                continue
            names = layer.fields().names()
            default = next((n for n in ('CODIGO','CLASSE','USO','TIPO_USO') if n in names), names[0])
            field, ok = QInputDialog.getItem(self, tr('Campo temático — ') + layer.name(),
                tr('Campo de classificação:'), names, names.index(default), False)
            if not ok:
                continue
            self.layer_combo.setLayer(layer)
            self.field_combo.setCurrentText(field)
            self.add_field()

    def add_field(self):
        layer = self._layer()
        field = self.field_combo.currentText()
        if not layer or not field:
            QMessageBox.warning(self, tr('Avaliação por sobreposição'),
                                tr('Selecione uma camada poligonal e o campo de classificação.'))
            return
        if layer.isEditable():
            QMessageBox.warning(self, tr('Camada em edição'),
                                tr('Salve ou descarte as edições da camada antes de adicioná-la.'))
            return
        if any(c['layer_id'] == layer.id() for c in self.criteria):
            QMessageBox.warning(self, tr('Camada já adicionada'),
                                tr('Cada mapa deve ser adicionado uma vez. Para avaliar vários campos '
                                'da mesma camada, utilize Avaliação vetorial por atributos.'))
            return
        counts = Counter()
        missing = 0
        for feature in layer.getFeatures():
            key = category_key(feature[field])
            if key is None:
                missing += 1
            else:
                counts[key] += 1
                if len(counts) > 256:
                    QMessageBox.warning(self, tr('Campo com muitas categorias'),
                                        tr(f'{layer.name()} / {field}: há mais de 256 categorias. '
                                        'Reclassifique valores contínuos antes da avaliação.'))
                    return
        if not counts:
            QMessageBox.warning(self, tr('Avaliação por sobreposição'),
                                tr('O campo não apresenta categorias válidas.'))
            return
        if self.criteria:
            previous = QgsProject.instance().mapLayer(self.criteria[0]['layer_id'])
            if previous is not None and layer.crs() != previous.crs():
                QMessageBox.warning(self, tr('SRC incompatível'),
                                    tr('Os mapas precisam ter o mesmo SRC. Reprojete a camada '
                                    'no QGIS antes de adicioná-la à avaliação.'))
                return
        self._save_classes()
        used = {c['field'] for c in self.criteria}
        index = 1
        while f'C{index:02d}' in used:
            index += 1
        self.criteria.append({
            'field': f'C{index:02d}', 'source_field': field,
            'layer_id': layer.id(), 'label': f'{layer.name()} → {field}',
            'counts': dict(counts), 'missing': missing, 'weight': 0.,
            'notes': {}, 'excluded': set(),
        })
        self._distribute()
        self._render_criteria(select=len(self.criteria) - 1)
        self.status.setText(tr('{count} mapa(s) na avaliação. ').format(count=len(self.criteria)) +
                            tr('Último mapa: {count} categorias; {missing} valores nulos.').format(count=len(counts), missing=missing))

    def _render_criteria(self, select=None):
        super()._render_criteria(select=select)
        for i, criterion in enumerate(self.criteria):
            self.criteria_table.item(i, 0).setText(criterion.get('label', criterion['field']))
        self._update_selection_title()

    def _criterion_selected(self):
        super()._criterion_selected()
        self._update_selection_title()

    def _update_selection_title(self):
        index = self.criteria_table.currentRow()
        if 0 <= index < len(self.criteria):
            c = self.criteria[index]
            self.class_label.setText(tr(f'{c["label"]}: {len(c["counts"])} categorias.'))

    def validate_configuration(self):
        try:
            self._rules()
            validate_overlay_plan(self.criteria)
            sources = validate_source_layers(self.criteria, QgsProject.instance())
            QMessageBox.information(self, tr('Sobreposição pronta'),
                tr(f'{len(sources)} camadas, {len(self.criteria)} critérios; pesos totalizam 100%.\n\n'
                'A saída representará SOMENTE áreas cobertas por todos os mapas. '
                'Sobreposições parciais e lacunas de cobertura podem reduzir a área avaliada. '
                'Feições com classes excluídas ou nulas permanecem, mas sem nota.'))
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, tr('Configuração incompleta'), tr(str(exc)))

    def select_output(self):
        suggestion = self.output_edit.text() or os.path.join(os.path.expanduser('~'), 'avaliacao_sobreposicao.gpkg')
        dest, _ = QFileDialog.getSaveFileName(self, tr('Salvar avaliação por sobreposição'),
                                              suggestion, 'GeoPackage (*.gpkg)')
        if dest:
            self.output_edit.setText(dest if dest.lower().endswith('.gpkg') else dest + '.gpkg')

    def execute(self):
        if self.running:
            return
        try:
            self._rules()
            validate_overlay_plan(self.criteria)
            validate_source_layers(self.criteria, QgsProject.instance())
            dest = (temporary_destination('avaliacao_sobreposicao', '.gpkg')
                    if self.temporary_check.isChecked() else self.output_edit.text().strip())
            if not dest:
                raise ValueError('Informe o GeoPackage de saída.')
            dest = os.path.abspath(dest)
            if os.path.exists(dest):
                if QMessageBox.question(
                    self, tr('Substituir resultado?'),
                    tr('O GeoPackage de saída já existe. Deseja substituí-lo?\n'
                    'Se estiver carregado no QGIS, remova a camada antiga antes de continuar.')
                ) != QMessageBox.StandardButton.Yes:
                    return
            self.running = True
            self.run_button.setEnabled(False)
            self.close_button.setEnabled(False)
            progress = QProgressDialog(tr('Sobrepondo camadas vetoriais…'), tr('Cancelar'), 0, 100, self)
            progress.setMinimumDuration(0)
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)

            def update(pct):
                if pct is not None:
                    progress.setValue(max(0, min(100, int(pct))))
                QApplication.processEvents()

            try:
                summary = evaluate_overlay(
                    self.criteria, int(self.scale_combo.currentData()), dest,
                    QgsProject.instance(), progress=update, cancelled=progress.wasCanceled,
                    report_csv=self.csv_check.isChecked(), report_txt=self.txt_check.isChecked())
            finally:
                progress.close()
            if self.load_check.isChecked() or self.temporary_check.isChecked():
                added = self.iface.addVectorLayer(dest, 'Vista Saga — Avaliação por sobreposição', 'ogr')
                if not added or not added.isValid():
                    self.status.setText(tr('Arquivo gerado, mas não foi possível carregá-lo no QGIS.'))
                    QMessageBox.warning(self, tr('Saída criada'),
                                        tr('O GeoPackage foi gerado, mas não pôde ser adicionado ao projeto.'))
                    return
            self.status.setText(tr('Avaliação por sobreposição concluída: ') + dest)
            QMessageBox.information(self, tr('Avaliação concluída'),
                tr(f'Camadas: {summary["camadas"]}\n'
                f'Polígonos resultantes: {summary["total"]}\n'
                f'Com nota: {summary["validos"]}\n'
                f'Sem nota: {summary["excluidos_ou_sem_dado"]}\n'
                f'Área total: {summary["area_total_ha"]:.4f} ha\n\n'
                f'Saída: {dest}\n\n'
                'Apenas a área de interseção comum foi avaliada.'
                + (f'\nCSV: {summary["relatorio_csv"]}' if summary.get('relatorio_csv') else '')
                + (f'\nTXT: {summary["relatorio_txt"]}' if summary.get('relatorio_txt') else '')))
        except (OSError, ValueError, TypeError, InterruptedError, RuntimeError) as exc:
            QMessageBox.warning(self, tr('Sobreposição não concluída'), tr(str(exc)))
        finally:
            self.running = False
            self.run_button.setEnabled(True)
            self.close_button.setEnabled(True)
