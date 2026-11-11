# Arquitetura e status das entregas — Novo Caged e INEP

Atualizado em 11/11/2026. O projeto usa Databricks Free Edition e arquitetura Medallion, com Landing, Bronze, Silver e Gold.

## Estado das entregas

| Entrega | Status e referência |
|---|---|
| Novo Caged | Ingestão e transformação versionadas. A fato Gold semestral foi validada no workspace em 31/10/2026 e cobre 2021S1–2026S1. |
| INEP | Censos de 2021 a 2024 processados em Bronze, Silver e Gold. As fatos Gold são anuais, com granularidade por rótulo CINE e recortes Brasil e UF. |
| Dimensões e correspondência CINE × CBO | Dimensões versionadas. A [bridge provisória](../../notebooks/03_analytics/034_bridge_provisoria_cine_cbo.ipynb) materializa a relação entre área específica CINE e subgrupo CBO e registra sua cobertura. |
| EDA | [Dashboard integrado](../eda/dashboard_unificado_caged_inep.html) com indicadores de emprego formal do Novo Caged e de graduação do Censo da Educação Superior do INEP. Os [resultados exploratórios](../../README.md#resultados-de-eda-e-machine-learning) estão resumidos no README. |
| Machine Learning | Wide Table mensal por competência × UF × subgrupo CBO, [backtest](../../notebooks/03_analytics/036_treino_backtest_admissoes.ipynb), previsões versionadas e análise de desalinhamento documentados no [glossário](../dicionario_dados/glossario_de_dados.md). |
| CI/CD | Validação automatizada e deploy do bundle em `dev` comprovados pelas execuções abaixo. A homologação operacional dos Jobs ponta a ponta segue pendente. |

## Orquestração no Databricks

O [`databricks.yml`](../../databricks.yml) define o bundle `mba_novo_caged`, inclui `resources/*.yml` e configura `dev` em modo de desenvolvimento como destino padrão.

| Job | Sequência versionada |
|---|---|
| [Caged](../../resources/job_caged.yml) | Verificação de novos arquivos (010) → Landing/Bronze (011) → Silver (020) → Gold semestral (030). |
| [INEP](../../resources/job_inep.yml) | Download (013) → Bronze (014) → Silver (024) → Gold anual (031). |
| [ML](../../resources/job_ml.yml) | Aguarda os Jobs Caged e INEP → gera features (035) → gera previsões (037) → analisa o desalinhamento (038). A configuração referencia a bridge provisória e uma versão do LightGBM no Model Registry. |

A bridge (034) e o backtest (036) têm notebooks próprios. A definição do Job de ML pressupõe a bridge e o modelo já disponíveis.

## Arquitetura de CI/CD

1. O [CI](../../.github/workflows/ci_validacao_aut_repo.yml) roda em PRs para `main`, em pushes para `main` e por acionamento manual. Valida a estrutura dos notebooks com `nbformat`, roda Ruff em `src` e `tests` e executa pytest, incluindo verificações locais de YAML, caminhos dos notebooks e dependências do bundle. Com `DATABRICKS_HOST` e `DATABRICKS_TOKEN` disponíveis, também roda `databricks bundle validate -t dev` com autenticação.
2. O [CD](../../.github/workflows/cd_databricks_dev.yml) recebe o evento `workflow_run` quando o CI termina. O job de deploy exige CI bem-sucedido originado de um push para `main`. Faz checkout do SHA validado, usa o ambiente GitHub `dev`, verifica a configuração de autenticação, revalida o bundle e executa `databricks bundle deploy -t dev --auto-approve --fail-on-active-runs`. A concorrência é controlada pelo grupo `databricks-bundle-dev`.
3. O deploy sincroniza arquivos e aplica os recursos do bundle. A execução dos Databricks Jobs ocorre por acionamento separado. O bundle exclui `notebooks/03_analytics/EDA.py` da sincronização para evitar a colisão com `EDA.ipynb`, que resolve para o mesmo caminho no workspace. CI e CD usam a CLI Databricks `1.24.0`. [Correção no PR #9](https://github.com/kevynzap/mba-novo-caged-data-engineering-free-edition/pull/9).

### Evidências de 11/11/2026

As duas execuções usaram o commit [`57fffe9`](https://github.com/kevynzap/mba-novo-caged-data-engineering-free-edition/commit/57fffe99084bf87c3308f566617ffdc42d36b219) da `main`.

| Execução | Resultado observado |
|---|---|
| [CI 43006642465](https://github.com/kevynzap/mba-novo-caged-data-engineering-free-edition/actions/runs/43006642465) | O job `Validate project` concluiu com sucesso. Os logs registram 24 notebooks validados, Ruff aprovado, validação autenticada do bundle em `dev` aprovada e 38 testes pytest aprovados. |
| [CD 43006689583](https://github.com/kevynzap/mba-novo-caged-data-engineering-free-edition/actions/runs/43006689583) | O job `Deploy Databricks Bundle to dev` concluiu com sucesso. O checkout usou o mesmo SHA do CI, a validação do bundle passou e a etapa `Deploy bundle (no job execution)` concluiu com sucesso. |

## Regras metodológicas

- Preservar a granularidade anual do INEP e respeitar a disponibilidade dos dados em cada corte da série mensal usada pelo ML.
- Controlar duplicações em relacionamentos CINE × CBO de muitos para muitos e preservar os códigos sem correspondência para análise de cobertura.
- Garantir idempotência, reconciliação de indicadores e rastreabilidade nas transformações.

## Pendências

- Registrar evidências de uma execução operacional ponta a ponta dos Databricks Jobs.
- Validar as fatos Gold do INEP contra as Sinopses Estatísticas oficiais e revisar a cobertura da bridge provisória.
