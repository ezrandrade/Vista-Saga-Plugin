"""Interface de Avaliação por sobreposição de VÁRIAS camadas vetoriais.

Aproveita as mesmas tabelas de notas e pesos já homologadas na avaliação de
atributos; apenas altera a fonte de cada critério e o processamento geométrico.
Cada camada entra uma vez, com o campo temático escolhido na importação: por
isso não há seletor de camada/campo à parte, como na guia Atributos.
"""
from .i18n import tr
from qgis.PyQt.QtWidgets import QHBoxLayout, QInputDialog, QMessageBox, QPushButton
from qgis.core import QgsProject

from .vector_evaluation_dialog import VectorEvaluationDialog, scan_categories
from .ui_shared import choose_project_layers, load_vector_source, open_polygon_files, vector_start_directory
from .vector_overlay_engine import validate_overlay_plan, validate_source_layers, evaluate_overlay

PREFERRED_FIELDS = ('CODIGO', 'CLASSE', 'USO', 'TIPO_USO')


class VectorOverlayEvaluationDialog(VectorEvaluationDialog):
    MODALITY = 'sobreposicao'
    WINDOW_TITLE = 'Vista Saga Plugin - Avaliação por sobreposição'
    HEADING = '<b>AVALIAÇÃO ESPACIAL - SOBREPOSIÇÃO DE MAPAS VETORIAIS</b>'
    INTRO = ('Adicione pelo menos duas camadas de polígonos, escolhendo um campo temático '
             'para cada mapa. Defina pesos e notas por classe. O plugin cruzará as geometrias '
             'e avaliará somente as regiões comuns a todas as camadas (interseção espacial). '
             'Os originais não serão modificados.')
    SOURCES_TITLE = '1. Camadas empilhadas e pesos'
    CLASSES_TITLE = '2. Classes da camada selecionada'
    CRITERION_HEADER = 'Camada → campo'
    EMPTY_CLASSES = 'Adicione um mapa e selecione-o na lista.'
    START_STATUS = 'Adicione duas ou mais camadas com SRC igual e área comum.'
    RESULT_PREFIX = 'avaliacao_sobreposicao'
    RESULT_NAME = 'Vista Saga - Avaliação por sobreposição'
    RUN_TEXT = 'Executar sobreposição e avaliação'

    def _build(self):
        super()._build()
        self.setMinimumSize(900, 625)

    def _build_source_controls(self, layout):
        row = QHBoxLayout()
        from_project = QPushButton(tr('Adicionar camadas do QGIS…'))
        from_project.setToolTip(tr('Escolhe uma ou várias camadas de polígonos já carregadas no QGIS.'))
        from_project.clicked.connect(self.add_project_many)
        row.addWidget(from_project)
        from_files = QPushButton(tr('Adicionar de arquivo(s)…'))
        from_files.setToolTip(tr('Abre camadas de polígonos em arquivo, a partir da pasta das '
                                 'camadas já carregadas no QGIS, e as adiciona ao projeto.'))
        from_files.clicked.connect(self.add_files)
        row.addWidget(from_files)
        remove = QPushButton(tr('Remover'))
        remove.clicked.connect(self.remove_field)
        row.addWidget(remove)
        row.addStretch(1)
        layout.addLayout(row)

    # Sem seletor de camada/campo: estes ganchos da classe base ficam neutros.
    def _populate_fields(self):
        pass

    def _layer_changed(self, _layer=None):
        pass

    def _layers_in_use(self):
        project = QgsProject.instance()
        layers = (project.mapLayer(c['layer_id']) for c in self.criteria)
        return [layer.source() for layer in layers if layer is not None]

    def add_project_many(self):
        self._add_layers(choose_project_layers(self, 'polygon', 'Empilhar mapas vetoriais'))

    def add_files(self):
        layers, warnings = open_polygon_files(self, 'Adicionar mapas vetoriais',
                                              vector_start_directory(self._layers_in_use()))
        self._add_layers(layers)
        if warnings:
            QMessageBox.warning(self, tr('Avaliação por sobreposição'), '\n'.join(warnings))

    def _add_layers(self, layers):
        for layer in layers:
            if any(c['layer_id'] == layer.id() for c in self.criteria):
                continue
            names = layer.fields().names()
            if not layer.isValid() or not names:
                continue
            default = next((n for n in PREFERRED_FIELDS if n in names), names[0])
            field, ok = QInputDialog.getItem(self, tr('Campo temático - ') + layer.name(),
                tr('Campo de classificação:'), names, names.index(default), False)
            if not ok:
                continue
            try:
                criterion = self._new_criterion(layer, field)
            except ValueError as exc:
                QMessageBox.warning(self, tr('Avaliação por sobreposição'), tr(str(exc)))
                continue
            self._append(criterion)
            self.status.setText(
                tr('{count} mapa(s) na avaliação. ').format(count=len(self.criteria)) +
                tr('Último mapa: {count} classes; {missing} valores nulos.').format(
                    count=len(criterion['counts']), missing=criterion['missing']))

    def _new_criterion(self, layer, field):
        if layer.isEditable():
            raise ValueError('Salve ou descarte as edições da camada antes de adicioná-la.')
        if any(c['layer_id'] == layer.id() for c in self.criteria):
            raise ValueError('Cada mapa deve ser adicionado uma vez. Para avaliar vários campos '
                             'da mesma camada, utilize Avaliação vetorial por atributos.')
        if self.criteria:
            previous = QgsProject.instance().mapLayer(self.criteria[0]['layer_id'])
            if previous is not None and layer.crs() != previous.crs():
                raise ValueError('Os mapas precisam ter o mesmo SRC. Reprojete a camada '
                                 'no QGIS antes de adicioná-la à avaliação.')
        counts, missing = scan_categories(layer, field)
        used = {c['field'] for c in self.criteria}
        index = 1
        while f'C{index:02d}' in used:
            index += 1
        return {'field': f'C{index:02d}', 'source_field': field,
                'layer_id': layer.id(), 'label': f'{layer.name()} → {field}',
                'counts': counts, 'missing': missing, 'weight': 0.,
                'notes': {}, 'excluded': set()}

    def _criterion_label(self, criterion):
        return criterion.get('label', criterion['field'])

    def _criterion_source(self, criterion):
        layer = QgsProject.instance().mapLayer(criterion['layer_id'])
        return (layer.name(), layer.source()) if layer is not None else (criterion['label'], '')

    def _criterion_field(self, criterion):
        return criterion['source_field']

    def _restore(self, records):
        problems = []
        self._clear_criteria()
        for rec in records:
            layer = load_vector_source(rec['fonte'], rec['camada']) if rec['fonte'] else None
            if layer is None:
                problems.append(tr('Camada não encontrada: {source}.').format(
                    source=rec['fonte'] or rec['camada']))
                continue
            if rec['campo'] not in layer.fields().names():
                problems.append(tr('{layer}: o campo {field} não existe.').format(
                    layer=layer.name(), field=rec['campo']))
                continue
            try:
                criterion = self._new_criterion(layer, rec['campo'])
            except ValueError as exc:
                problems.append(tr(str(exc)))
                continue
            problems.extend(self._apply_record(criterion, rec))
        return problems

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

    def _check_inputs(self):
        self._rules()
        validate_overlay_plan(self.criteria)
        validate_source_layers(self.criteria, QgsProject.instance())

    def _run_engine(self, dest, update, cancelled):
        return evaluate_overlay(
            self.criteria, self._scale(), dest,
            QgsProject.instance(), progress=update, cancelled=cancelled,
            report_csv=self.csv_check.isChecked(), report_txt=self.txt_check.isChecked())

    def _summary_text(self, summary, dest):
        return tr(f'Camadas: {summary["camadas"]}\n'
                  f'Polígonos resultantes: {summary["total"]}\n'
                  f'Com nota: {summary["validos"]}\n'
                  f'Sem nota: {summary["excluidos_ou_sem_dado"]}\n'
                  f'Área total: {summary["area_total_ha"]:.4f} ha\n\n'
                  f'Saída: {dest}\n\n'
                  'Apenas a área de interseção comum foi avaliada.')
