# MBA Engenharia de Dados — Previsão de Demanda Profissional e Formação Educacional no Brasil

**Instituição:** Universidade Presbiteriana Mackenzie  
**Projeto:** Engenharia de Dados aplicada aos microdados do Novo Caged e Educação Formal

**Organização Trabalho via Trello:** https://trello.com/invite/b/6aca28ac2b79adb2bdb0327f/ATTI0613962c5f2f6d8644243304ce2c6644C3F64287/mba-previsao-da-demanda-por-ocupacoes

**Problema de Negócio:** Instituições de ensino, organizações de formação profissional e gestores públicos precisam planejar a oferta de cursos diante das mudanças no mercado de trabalho, mas os indicadores de emprego e educação estão distribuídos em fontes, metodologias diferentes e possuem frequências de atualização distintas.

**Pergunta Central:** Como utilizar dados históricos do emprego formal e da educação profissional para prever a evolução das admissões por ocupação e região e apoiar decisões de planejamento da formação profissional no Brasil?

## OBJETIVOS
Desenvolver uma solução de Engenharia de Dados e Machine Learning para analisar e prever tendências de admissões no mercado de trabalho formal brasileiro, relacionando os resultados à oferta de educação profissional.

**Objetivos Específicos:**
Ingerir e integrar dados públicos de emprego e educação.
- Implementar um Lakehouse com camadas de dados brutos, tratados e analíticos.
- Construir um modelo dimensional para análises históricas e uma tabela analítica para Machine Learning.
- Treinar e avaliar modelos de previsão mensal de admissões por UF e grupo ocupacional.
- Criar um dashboard para acompanhar previsões, tendências e indicadores educacionais.
- Demonstrar arquitetura Lambda, CI/CD, qualidade e versionamento.

## DESENHO INICIAL DA ARQUITETURA
A sugestão para o desenvolvimento desse projeto, e uma arquitetura que contemple os seguintes requisitos para a arquitetura Lambda, Star Schema, Wide Table, CI/CD. Assim, a escolha inicial será a atualização de Databricks Free Edition, com armazenamento Delta Lake, garantindo consistência para o processamento distribuído, pipelines batch, streaming e Machine Learning.
- Landing: Camada para capturar os dados das fontes de origem.
- Bronze: preservar os arquivos originais e registrar a origem, data de ingestão e versão.
- Silver: padronizar tipos de dados, validar códigos, tratar registros inválidos e normalizar datas, UFs e ocupações.
- Gold: gerar indicadores agregados, modelo dimensional e dados prontos para previsão.
- Batch: processar todo o histórico e recalcular resultados quando necessário.

  <img width="755" height="567" alt="image" src="https://github.com/user-attachments/assets/3a292e32-9cca-4d3c-bb29-e54a616cde62" />


## ARQUITETURA
| Componente | Tecnologia Proposta | Responsabilidade |
|---|---:|
| Armazenamento | Databricks Volumes | Armazenar arquivos e dados do Lakehouse |
| Processamento | Azure Databricks + PySpark | Ingestão, transformações distribuídas e batch |
| Formato de dados | Delta Lake | Armazenamento transacional e evolução de tabelas |
| Machine Learning | Python + scikit-learn |Treinar e avaliar modelos de previsão |
| BI | Power BI | Dashboard executivo |
| Versionamento | Git + GitHub | Código, documentação e histórico |
| CI/CD | GitHub Actions | Testes automatizados e validações de deploy |
| Qualidade | pytest + regras de validação de dados | Verificar código, esquemas e integridade |
| Organização | Trello | Kanban, prioridades e acompanhamento de tarefas |

Os arquivos brutos e a extração temporária ficam em um volume do Unity Catalog. O código atual não depende de provisionamento de ADLS Gen2 nem contém configuração funcional de Terraform. As tabelas são gravadas pelo nome no catálogo, sem localização externa explícita.

## ESTRUTURA DO REPOSITÓRIO

```text
docs/
  dicionario-dados-novo-caged-movimentacao.xlsx
notebooks/
  00_setup/
    01_create_catolog_schema.ipynb
    02_commom_functions.py
  01_ingestao/
    00_verificar_novos_arquivos.ipynb
    01_landing_to_bronze.ipynb
  02_transformacao/
    01_dicionarios_referencia.ipynb
  03_analytics/                # notebook vazio
infrastructure/terraform/     # notebook vazio; sem arquivos Terraform
src/transformations/          # notebook vazio
tests/                        # test_bronze e test_silver vazios
```

Essas verificações não substituem testes automatizados. Os arquivos em `tests/` ainda estão vazios.

## Limitações e próximos passos

- Validação dos dados na camada Gold.
- Validar a implementação dos testes de qualidade, atualização das referências e tratamento de falhas.
- Versionar a configuração dos jobs e definir a estratégia para revisões de competências já ingeridas; a descoberta atual ignora meses que já constam na Bronze.
