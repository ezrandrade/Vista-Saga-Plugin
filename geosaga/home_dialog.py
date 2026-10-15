"""Painel de acesso aos módulos do Vista Saga Plugin (QGIS 4 / Qt6).

O painel reúne sete módulos com a mesma apresentação e navegação.
"""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)


class HomeDialog(QDialog):
    """Painel inicial sem estado de dados, para não interferir na avaliação."""

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle('Vista Saga Plugin — Painel de módulos')
        self.setModal(False)
        self.setMinimumSize(820, 590)
        self.resize(1010, 780)
        self.setObjectName('vistaSagaHome')
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        header = QLabel('Vista Saga Plugin')
        header.setObjectName('vistaSagaTitle')
        root.addWidget(header)
        description = QLabel(
            'Escolha um módulo para começar.\n'
            'Uma nova janela será aberta para cada módulo.'
        )
        description.setObjectName('vistaSagaDescription')
        description.setWordWrap(True)
        root.addWidget(description)

        # Os sete módulos possuem cartões idênticos em apresentação e acesso.
        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        cards.setVerticalSpacing(12)
        modules = [
            ('01', 'Assinatura',
             'Quantifique classes temáticas em áreas de interesse, com estatísticas e áreas.',
             'Abrir assinatura', self.plugin.open_signature),
            ('02', 'Monitoria',
             'Compare períodos, identifique permanências e mudanças e gere matrizes e relatórios.',
             'Abrir monitoria', self.plugin.open_monitoring),
            ('03', 'Avaliação',
             'Cruze critérios por pesos e notas. Avaliação raster ou vetorial por atributos e sobreposição.',
             'Abrir avaliação', self.plugin.open_interactive),
            ('04', 'Análises Voronoi',
             'Delimite áreas de influência: simples, massa, atrito e massa com atrito.',
             'Abrir Voronoi', self.plugin.open_voronoi),
            ('05', 'Combinação de Mapas',
             'Combine categorias de mapas raster ou vetoriais e calcule áreas e percentuais.',
             'Abrir combinação', self.plugin.open_combination),
            ('06', 'Conversão de Formatos',
             'Converta RS2, GeoTIFF e vetores; rasterize ou vetorize mapas.',
             'Abrir conversor', self.plugin.open_rs2_converter),
            ('07', 'Sequenciador de Mapas',
             'Anime mapas raster, vetoriais ou mistos por período; exporte GIF e quadros PNG.',
             'Abrir sequenciador', self.plugin.open_sequence),
        ]

        for index, (number, name, desc, action, callback) in enumerate(modules):
            self._add_card(cards, index // 3, index % 3, number, name, desc, action, callback)
        for column in range(3):
            cards.setColumnStretch(column, 1)
        root.addLayout(cards, stretch=1)

        note = QLabel(
            'Projeto independente inspirado nos procedimentos do Vista SAGA/UFRJ. '
            'Não contém código do programa original. '
            'Confira os resultados antes de utilizá-los em estudos técnicos.\n'
            'Desenvolvedor: Esdras Andrade — Instituto de Geografia, Desenvolvimento '
            'e Meio Ambiente (IGDEMA), Universidade Federal de Alagoas (UFAL).'
        )
        note.setObjectName('vistaSagaFootnote')
        note.setWordWrap(True)
        root.addWidget(note)

        footer = QHBoxLayout()
        footer.addStretch(1)
        close = QPushButton('Fechar painel')
        close.setObjectName('vistaSagaClose')
        close.clicked.connect(self.close)
        footer.addWidget(close)
        root.addLayout(footer)

    def _add_card(self, layout, row, column, number, title, description, button_text, callback):
        card = QFrame()
        card.setObjectName('vistaSagaCard')
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contents = QVBoxLayout(card)
        contents.setContentsMargins(17, 17, 17, 17)
        contents.setSpacing(11)
        number_label = QLabel(number)
        number_label.setObjectName('vistaSagaNumber')
        contents.addWidget(number_label)
        title_label = QLabel(title)
        title_label.setObjectName('vistaSagaCardTitle')
        title_label.setWordWrap(True)
        contents.addWidget(title_label)
        description_label = QLabel(description)
        description_label.setObjectName('vistaSagaCardDescription')
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        contents.addWidget(description_label, 1)
        action = QPushButton(button_text)
        action.setObjectName('vistaSagaAction')
        action.clicked.connect(callback)
        contents.addWidget(action)
        layout.addWidget(card, row, column)

    def _apply_theme(self):
        # Estilos apenas dentro deste diálogo; não modificam o tema do QGIS.
        is_dark = self.palette().window().color().lightness() < 128
        if is_dark:
            panel, card, border = '#252c31', '#303940', '#56616b'
            ink, muted, accent, button_ink = '#edf2f4', '#b9c7ce', '#74c7be', '#132623'
        else:
            panel, card, border = '#f5f7f8', '#ffffff', '#d5dfe4'
            ink, muted, accent, button_ink = '#20313c', '#516570', '#006b65', '#ffffff'
        self.setStyleSheet('''
            QDialog#vistaSagaHome { background: %(panel)s; }
            QLabel#vistaSagaTitle { color: %(ink)s; font-size: 24px; font-weight: 700; }
            QLabel#vistaSagaSubtitle { color: %(accent)s; font-size: 13px; font-weight: 600; }
            QLabel#vistaSagaDescription, QLabel#vistaSagaFootnote {
                color: %(muted)s; font-size: 12px; }
            QFrame#vistaSagaCard { background: %(card)s; border: 1px solid %(border)s;
                border-radius: 10px; }
            QLabel#vistaSagaNumber { color: %(accent)s; font-size: 22px; font-weight: 700;
                border: none; }
            QLabel#vistaSagaCardTitle { color: %(ink)s; font-size: 15px;
                font-weight: 700; border: none; }
            QLabel#vistaSagaCardDescription, QLabel#vistaSagaCardStatus {
                color: %(muted)s; border: none; font-size: 12px; }
            QLabel#vistaSagaCardStatus { font-weight: 600; }
            QPushButton#vistaSagaAction { background: %(accent)s; color: %(button_ink)s;
                border: 1px solid %(accent)s; border-radius: 5px; padding: 9px 8px;
                font-weight: 600; }
            QPushButton#vistaSagaAction:hover { border: 2px solid %(ink)s; }
            QPushButton#vistaSagaClose { padding: 6px 15px; }
        ''' % locals())
