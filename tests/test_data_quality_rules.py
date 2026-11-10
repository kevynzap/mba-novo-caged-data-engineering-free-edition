"""Testes de regras ja implementadas em Bronze, Silver e Gold.

Sem cluster Databricks: executa funcoes puras do proprio notebook CAGED e
verifica contratos de seguranca/qualidade dos demais notebooks.
Nao substitui testes Spark com datasets reais ou sinteticos.
"""

import ast
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def codigo_notebook(caminho):
    notebook = json.loads((ROOT / caminho).read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def obter_definicoes_caged():
    """Extrai as funcoes reais de geracao SQL do notebook, sem executar Spark."""
    codigo = codigo_notebook("notebooks/02_transformacao/020_bronze_to_silver_caged.ipynb")
    arvore = ast.parse(codigo[codigo.index("def num("):codigo.index("# (nome_silver, tipo, expressão")])
    funcoes = [node for node in arvore.body if isinstance(node, ast.FunctionDef)]
    namespace = {}
    exec(compile(ast.Module(body=funcoes, type_ignores=[]), "<caged-silver>", "exec"), namespace)
    return namespace


@pytest.mark.parametrize(
    ("coluna", "tipo", "esperado"),
    [
        ("idade", "SMALLINT", "try_cast(`idade` AS SMALLINT)"),
        ("município", "INT", "try_cast(`município` AS INT)"),
        ("saldomovimentação", "SMALLINT", "try_cast(`saldomovimentação` AS SMALLINT)"),
    ],
)
def test_silver_caged_funcao_num(coluna, tipo, esperado):
    assert obter_definicoes_caged()["num"](coluna, tipo) == esperado


def test_silver_caged_funcao_decimal_aceita_virgula_e_preserva_nulo():
    sql = obter_definicoes_caged()["dec"]("salário")
    assert "replace(`salário`, ',', '.')" in sql
    assert "try_cast" in sql
    assert "DECIMAL(20,4)" in sql
    assert "round(" in sql
    assert sql.endswith(", 2)")


@pytest.mark.parametrize("coluna", ["competênciamov", "competênciadec"])
def test_silver_caged_funcao_competencia(coluna):
    sql = obter_definicoes_caged()["comp"](coluna)
    assert sql == f"to_date(concat(`{coluna}`, '01'), 'yyyyMMdd')"


def test_bronze_caged_valida_competencia_e_nao_grava_arquivo_vazio():
    codigo = codigo_notebook("notebooks/01_ingestao/011_landing_to_bronze_caged.ipynb")
    assert "_competencia_referencia" in codigo
    assert "competênciamov" in codigo
    assert 'assert resumo_val["total"] > 0' in codigo
    assert 'assert resumo_val["invalidos"] == 0' in codigo


def test_silver_caged_preserva_linhas_repetidas_sem_deduplicar():
    codigo = codigo_notebook("notebooks/02_transformacao/020_bronze_to_silver_caged.ipynb")
    assert "LEFT JOIN workspace.bronze." in codigo
    assert ".overwrite(F.col(\"competencia_referencia\") == comp)" in codigo
    # Verifica o comportamento do codigo (sem exigir texto em celulas Markdown).
    assert "dropDuplicates(" not in codigo


def test_gold_caged_separa_admissoes_desligamentos_e_reconcilia():
    codigo = codigo_notebook("notebooks/03_analytics/030_silver_to_gold_caged.ipynb")
    assert 'F.col("saldo_movimentacao") == 1' in codigo
    assert 'F.col("saldo_movimentacao") == -1' in codigo
    assert 'F.count(F.lit(1)).alias("total_movimentacoes")' in codigo
    assert 'F.sum("saldo_movimentacao").alias("saldo")' in codigo
    assert 'assert resumo_fato["admissoes"] == resumo_silver["admissoes"]' in codigo
    assert 'assert resumo_fato["desligamentos"] == resumo_silver["desligamentos"]' in codigo
    assert 'assert resumo_fato["movimentacoes"] == resumo_silver["movimentacoes"]' in codigo
    assert 'assert resumo_fato["saldo"] == resumo_silver["saldo"]' in codigo


def test_gold_caged_somente_semestres_com_seis_meses():
    codigo = codigo_notebook("notebooks/03_analytics/030_silver_to_gold_caged.ipynb")
    assert "MESES_SEMESTRE = 6" in codigo
    assert 'F.countDistinct("mes").alias("meses_presentes")' in codigo
    assert 'F.col("meses_presentes") == MESES_SEMESTRE' in codigo
    assert "semestres_completos" in codigo


def test_inep_silver_conserva_chaves_e_rastreabilidade():
    codigo = codigo_notebook("notebooks/02_transformacao/024_bronze_to_silver_inep.ipynb")
    assert '"CO_CINE_ROTULO": "codigo_cine_rotulo"' in codigo
    assert '"NU_ANO_CENSO": "ano_censo"' in codigo
    assert '"hash_origem": "hash_origem"' in codigo
    assert '"TP_DIMENSAO": "tipo_dimensao"' in codigo
    assert "anos_pendentes" in codigo


@pytest.mark.parametrize(
    ("indicador", "dimensoes"),
    [
        ("ingressantes", [1, 2]),
        ("matriculas", [1, 2]),
        ("concluintes", [1, 2]),
        ("cursos", [1, 3]),
        ("vagas", [1, 3]),
        ("inscritos", [1, 3]),
    ],
)
def test_gold_inep_brasil_dimensoes_por_indicador(indicador, dimensoes):
    codigo = codigo_notebook("notebooks/03_analytics/031_silver_to_gold_inep.ipynb")
    inicio = codigo.index("metricas = {")
    fim = codigo.index("# Totais esperados calculados na Silver", inicio)
    trecho = codigo[inicio:fim].strip()
    arvore = ast.parse(trecho)
    atribuicao = next(
        n for n in arvore.body
        if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "metricas" for t in n.targets
        )
    )
    mapeamento = ast.literal_eval(atribuicao.value)
    assert mapeamento[indicador][1] == dimensoes


def test_gold_inep_uf_exclui_ead_nacional_e_valida_chave():
    codigo = codigo_notebook("notebooks/03_analytics/031_silver_to_gold_inep.ipynb")
    assert 'F.col("tipo_dimensao").isin(1, 2)' in codigo
    assert 'F.col("tipo_dimensao") == 1' in codigo
    assert '"codigo_cine_rotulo"' in codigo
    assert 'qtd_duplicados > 0' in codigo
    assert "replaceWhere" in codigo


def test_pipeline_sem_dependencia_de_mapeamento_mec():
    """Pipeline principal atual: ingestion CAGED/INEP e Gold, sem bridge MEC."""
    caminhos = [
        "notebooks/01_ingestao/011_landing_to_bronze_caged.ipynb",
        "notebooks/02_transformacao/020_bronze_to_silver_caged.ipynb",
        "notebooks/02_transformacao/024_bronze_to_silver_inep.ipynb",
        "notebooks/03_analytics/030_silver_to_gold_caged.ipynb",
        "notebooks/03_analytics/031_silver_to_gold_inep.ipynb",
    ]
    for caminho in caminhos:
        codigo = codigo_notebook(caminho)
        assert "bridge_cine_cbo_provisoria" not in codigo
        assert "workspace.gold.bridge_cine_cbo" not in codigo
