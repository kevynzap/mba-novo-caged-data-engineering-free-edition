# Arquitura dos Pipelines - Novo Caged e INEP
**Atualização:** 29/10/2026
**Ambiente:** Databricks Free Edition
**Arquitetura:** Medallion - Landing, Bronze, Silver e Gold

## 1. Estado das Entregas

**Novo Caged**
- **010_verificar_novos_arquivos_caged:** realiza uma verificação no FTP para identificar novos arquivos.
- **011_landing_to_bronze:** extração e persitência dos dados na camada bronze.
- **012_dicionarios_referencia_caged:** leitura e captura de um arquivo .xlsx referente ao dicionario de dados do caged (docs/dicionario_dados) e persistência dos dados na camada bronze.
- **020_bronze_to_silver_caged:** tratamento e validação.
- **021_analise_qualidade_bronze_caged:** analise da qualidade dos dados contidos na camada bronze para posterior criação da delta na camada silver (020_bronze_to_silver_caged).
- **022_bronze_to_silver_ref_caged:** criação da camada silver das dimensões de referência do caged.
- **030_silver_to_gold_caged:** construção da camada analitica com granularidade semestral.


**INEP - Educação Superior**
- **013_donwload_landing_inep:** captura dos microdados oficiais.
- **014_landing_to_bronze_inep:** extração e persistência bronze.
- **024_bronze_to_silver_inep:** tratamento e validação.
- **031_silver_to_gold_inep:** geração de duas golds anuais, por UF e Brasil, com granularidade por rótulo CINE.
- Processamento analítico dos anos 2021 - 2024 homologando funcionalmente pelo responsável.

**Dimensões:**
- 032_preparacao_dimensoes_cine_cbo concluído.
- dim_cine_brasil: 372 rótulos únicos.
- dim_cbo_ocupacao: 2.778 códigos ocupacionais.
- Inditificados 41 códigos CBO na Gold Caged sem correspondência na dimensão.

**Correspondência CINE-CBO**
- 033_construcao_bridge_cine_cbo: implementação planejada, aguardando resposta do Fala.BR com dados de relação metodológica para relacionar fontes de dados.

## 2. Sequência dos Jobs
**Job Caged:** Landing -> Bronze -> Silver -> Gold semestral.
**Job INEP:** 013 -> 014 -> 024 -> 031.
**Job Dimensões:** 032, após atualização das fontes INEP e CBO.
**Job Correspondência:** 033, somente após disponibilização e validação da matriz.
**Job Integração:** Wide Table semestral, após Golds e bridge homologadas.

## 3. Regras Metodológicas
- INEP permanece anula; não gerar indicadores mensais artificiais.
- A integração semestral deve respeitar a data efetiva de disponibilidade do INEP.
- Não duplicar indicadores educacionais em relacionamentos N para N no CINE-CBO.
- Preservar os códigos ocupacionais sem DE-PARA para análise de cobertura.
- Garantir idempotência, reconciliação de indicadores e rastreabilidade das transformações.

## 4. Pendências
- Documentar evidências completas da orquestração dos Jobs.
- Validar as Golds INEP com as Sinopses Estatísticas oficiais.
- Concluir e revisão da qualidade da gold Caged.
- Receber e validar a matriz CINE-CBO.
- Definir o relacionamento temporal e construir a Wide Table.
- Desenvolver e avaliar o modelo preditivo.