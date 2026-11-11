"""Valida estrutura e referências locais dos Databricks Bundles, sem credenciais.

Nao substitui 'databricks bundle validate': a etapa completa executa com
autenticacao Databricks, quando configurada no GitHub Actions.
"""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "databricks.yml"
RECURSOS = ROOT / "resources"
JOBS_ESPERADOS = {"job_caged", "job_inep", "job_ml"}


def carregar_yaml(path):
    with path.open(encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def test_bundle_inclui_recursos():
    bundle = carregar_yaml(BUNDLE)
    assert bundle["bundle"]["name"] == "mba_novo_caged"
    assert "resources/*.yml" in bundle["include"]
    assert "dev" in bundle["targets"]


def test_recursos_job_declaram_tarefas_validas():
    jobs = {}
    for caminho in RECURSOS.glob("*.yml"):
        recurso = carregar_yaml(caminho)
        assert isinstance(recurso, dict), f"{caminho}: YAML vazio"
        for chave, job in recurso.get("resources", {}).get("jobs", {}).items():
            assert chave not in jobs, f"Job duplicado: {chave}"
            assert job.get("tasks"), f"{chave}: sem tasks"
            jobs[chave] = job

    assert JOBS_ESPERADOS <= jobs.keys()

    for chave, job in jobs.items():
        tarefas = job["tasks"]
        keys = [t["task_key"] for t in tarefas]
        assert len(keys) == len(set(keys)), f"{chave}: task_key duplicada"
        for tarefa in tarefas:
            for dep in tarefa.get("depends_on", []):
                assert dep["task_key"] in keys, (
                    f"{chave}/{tarefa['task_key']}: dependencia inexistente"
                )
            if "notebook_task" in tarefa:
                notebook = tarefa["notebook_task"]["notebook_path"]
                arquivo = (RECURSOS / notebook).resolve()
                assert arquivo.is_relative_to(ROOT), f"{chave}: caminho fora do repo"
                assert arquivo.is_file(), f"{chave}: notebook ausente: {notebook}"


def test_job_ml_depois_das_fontes():
    job = carregar_yaml(RECURSOS / "job_ml.yml")["resources"]["jobs"]["job_ml"]
    tasks = {t["task_key"]: t for t in job["tasks"]}
    assert tasks["atualizar_caged"]["run_job_task"]["job_id"] == (
        "${resources.jobs.job_caged.id}"
    )
    assert tasks["atualizar_inep"]["run_job_task"]["job_id"] == (
        "${resources.jobs.job_inep.id}"
    )
    assert {d["task_key"] for d in tasks["gerar_features_ml"]["depends_on"]} == {
        "atualizar_caged", "atualizar_inep"
    }
    assert tasks["gerar_previsoes"]["depends_on"] == [
        {"task_key": "gerar_features_ml"}
    ]
    assert tasks["analisar_desalinhamento"]["depends_on"] == [
        {"task_key": "gerar_previsoes"}
    ]
