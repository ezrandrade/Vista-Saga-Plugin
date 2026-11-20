"""Vetor -> RS2 (correção na 1.5.0): nenhum dataset GDAL temporário fica aberto até a limpeza.

No Windows, arquivo aberto não pode ser apagado: a variável do laço que prepara as grades mantinha o
``cobertura.tif`` aberto, e a pasta ``.vista_vector_rs2_*`` ficava na pasta de saída (teste do autor,
20/11/2026). No Linux o defeito não aparece, por isso a verificação é estrutural.
"""
import ast
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'vector_rs2.py'


class VetorRs2Temporarios150(unittest.TestCase):
    def test_variavel_do_laco_das_grades_e_liberada(self):
        tree = ast.parse(SRC.read_text(encoding='utf-8'))
        function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                        and n.name == 'convert_vector_to_rs2')
        for body in (n for n in ast.walk(function) if hasattr(n, 'body') and isinstance(n.body, list)):
            for i, node in enumerate(body.body):
                if (isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                        and 'cover_ds' in ast.unparse(node.iter)):
                    name = node.target.id
                    released = any(isinstance(after, ast.Assign) and ast.unparse(after).startswith(f'{name} = ')
                                   and isinstance(after.value, ast.Constant) and after.value.value is None
                                   for after in body.body[i + 1:])
                    self.assertTrue(released, f'{name} continua referenciando cover_ds')
                    return
        self.fail('laço das grades temporárias não encontrado')


if __name__ == '__main__':
    unittest.main()
