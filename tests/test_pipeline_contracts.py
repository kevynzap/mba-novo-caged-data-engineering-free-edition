"""Contract checks for the versioned Databricks notebooks.

These checks run without a Spark cluster. They validate repository-level
contracts, not the correctness of transformations on real data.
"""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "notebooks" / "03_analytics"


def notebook_code(filename):
    """Collect source code from code cells without evaluating Databricks magics."""
    path = ANALYTICS / filename
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["cells"], f"{filename}: notebook vazio"
    return "\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source", []), list)
        else cell.get("source", "")
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


@pytest.mark.parametrize(
    ("filename", "sources", "targets"),
    [
        (
            "030_silver_to_gold_caged.ipynb",
            ["workspace.silver.novo_caged_movimentacoes"],
            ["workspace.gold.fato_caged_semestral"],
        ),
        (
            "031_silver_to_gold_inep.ipynb",
            ["workspace.silver.inep_superior_cursos"],
            [
                "workspace.gold.fato_inep_educacao_uf_anual",
                "workspace.gold.fato_inep_educacao_brasil_anual",
            ],
        ),
        (
            "032_mapeamento_cine_cbo.ipynb",
            ["workspace.silver.ref_cbo_ocupacao"],
            ["workspace.gold.dim_cine_brasil", "workspace.gold.dim_cbo_ocupacao"],
        ),
        (
            "033_construcao_bridge_cine_cbo.ipynb",
            ["workspace.gold.dim_cine_brasil", "workspace.gold.dim_cbo_ocupacao"],
            ["workspace.gold.bridge_cine_cbo"],
        ),
        (
            "035_gold_ml_features.ipynb",
            [
                "workspace.silver.novo_caged_movimentacoes",
                "workspace.gold.fato_inep_educacao_uf_anual",
            ],
            ["workspace.gold.ml_features_mensal_uf_cbo"],
        ),
        (
            "036_treino_backtest_admissoes.ipynb",
            ["workspace.gold.ml_features_mensal_uf_cbo"],
            ["workspace.gold.ml_backtest_admissoes"],
        ),
        (
            "037_previsoes_operacionais.ipynb",
            ["workspace.gold.ml_features_mensal_uf_cbo"],
            ["workspace.gold.previsoes_admissoes"],
        ),
        (
            "038_desalinhamento_formacao_mercado.ipynb",
            [
                "workspace.gold.previsoes_admissoes",
                "workspace.gold.fato_inep_educacao_uf_anual",
            ],
            ["workspace.gold.desalinhamento_formacao_mercado"],
        ),
    ],
)
def test_lineage_contract(filename, sources, targets):
    code = notebook_code(filename)
    for table in sources + targets:
        assert table in code, f"{filename}: tabela esperada ausente: {table}"


def test_caged_semester_requires_completeness_and_reconciliation():
    code = notebook_code("030_silver_to_gold_caged.ipynb")
    assert "meses" in code.lower()
    assert "chaves_duplicadas" in code
    assert "saldo_movimentacao" in code


def test_inep_gold_incremental_year_partition_contract():
    code = notebook_code("031_silver_to_gold_inep.ipynb")
    assert "replaceWhere" in code
    assert "ano_censo" in code
    assert "identificar_pendencias" in code


def test_official_bridge_stops_when_source_is_missing():
    code = notebook_code("033_construcao_bridge_cine_cbo.ipynb")
    assert 'STATUS_AGUARDANDO = "AGUARDANDO_FONTE"' in code
    assert "if not arquivos_csv:" in code
    assert "dbutils.notebook.exit(STATUS_AGUARDANDO)" in code
    assert "df_mapeamento_valido" in code


def test_ml_pipeline_marks_mapping_as_provisional():
    for filename in (
        "035_gold_ml_features.ipynb",
        "038_desalinhamento_formacao_mercado.ipynb",
    ):
        code = notebook_code(filename)
        assert "workspace.gold.bridge_cine_cbo_provisoria" in code


def test_training_and_forecast_use_distinct_versioned_outputs():
    training = notebook_code("036_treino_backtest_admissoes.ipynb")
    forecast = notebook_code("037_previsoes_operacionais.ipynb")
    assert "versao_backtest" in training
    assert "versao_previsao" in forecast
    assert "horizonte" in forecast.lower()
