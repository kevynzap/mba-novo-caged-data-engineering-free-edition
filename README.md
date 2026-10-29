# MBA Engenharia de Dados — Previsão de Demanda Profissional e Formação Educacional no Brasil

**Instituição:** Universidade Presbiteriana Mackenzie  
**Projeto:** Engenharia de Dados aplicada aos microdados do Novo Caged e Educação Formal

**Organização do trabalho:** [Trello — MBA | Previsão da Demanda por Ocupações](https://trello.com/b/sts8EjN4)

**Documentação Status Projeto:** docs/status_entregas

## Problema de negócio

Instituições de ensino, organizações de formação profissional e gestores públicos precisam planejar a oferta de cursos diante das mudanças no mercado de trabalho, mas os indicadores de emprego e educação estão distribuídos em fontes e metodologias diferentes e possuem frequências de atualização distintas.

**Pergunta central:** Como utilizar dados históricos do emprego formal e da educação profissional para prever a evolução das admissões por ocupação e região e apoiar decisões de planejamento da formação profissional no Brasil?

## Objetivos

Desenvolver uma solução de Engenharia de Dados e Machine Learning para analisar e prever tendências de admissões no mercado de trabalho formal brasileiro, relacionando os resultados à oferta de educação profissional.

### Objetivos específicos

- Ingerir e integrar dados públicos de emprego e educação.
- Implementar um Lakehouse com camadas de dados brutos, tratados e analíticos.
- Construir um modelo dimensional para análises históricas e uma tabela analítica para Machine Learning.
- Treinar e avaliar modelos de previsão de admissões por UF e grupo ocupacional, considerando a compatibilização temporal com os dados educacionais.
- Criar um dashboard para acompanhar previsões, tendências e indicadores educacionais.
- Demonstrar arquitetura Lambda, CI/CD, qualidade e versionamento, conforme os requisitos acadêmicos e as possibilidades dos ambientes utilizados.

## Desenho inicial da arquitetura

O projeto adota uma arquitetura **Lakehouse baseada no padrão Medallion**, estruturando os dados em Landing, Bronze, Silver e Gold.

A solução utiliza atualmente **Databricks Free Edition**, Apache Spark, Unity Catalog e Delta Lake. O processamento desenvolvido até o momento é predominantemente **batch**, adequado à publicação periódica dos microdados do Novo Caged.

A arquitetura considera os requisitos de Lambda, Star Schema, Wide Table, CI/CD e Machine Learning, distinguindo os componentes já implementados daqueles previstos para as próximas etapas.

- **Landing:** recepção e preservação dos arquivos oficiais disponibilizados pelas fontes.
- **Bronze:** ingestão dos microdados e dicionários de referência, com preservação dos valores de origem e metadados de rastreabilidade.
- **Silver:** padronização de nomes e tipos, tratamento de formatos, enriquecimento com descrições e validações de qualidade.
- **Gold:** construção de fatos e indicadores analíticos destinados a consultas, visualizações e modelagem preditiva.
- **Batch:** processamento dos dados históricos e das novas competências publicadas.
- **Streaming / Lambda:** requisito arquitetural a ser avaliado e demonstrado posteriormente; não corresponde a um fluxo de streaming já implementado.

### Diagrama da arquitetura

<img width="755" height="567" alt="Desenho da arquitetura de dados do projeto" src="https://github.com/user-attachments/assets/3a292e32-9cca-4d3c-bb29-e54a616cde62" />

## Arquitetura técnica

| Componente | Tecnologia | Responsabilidade |
|---|---|---|
| Ambiente principal | Databricks Free Edition | Desenvolvimento e execução dos pipelines |
| Armazenamento de arquivos | Unity Catalog Volumes | Preservação dos arquivos originais e staging de extração |
| Processamento | Apache Spark / PySpark / Spark SQL | Ingestão, transformação e agregação distribuída |
| Armazenamento analítico | Delta Lake | Persistência transacional das tabelas |
| Catálogo | Unity Catalog | Organização dos schemas e das tabelas |
| Orquestração | Databricks Jobs | Encadeamento das atividades de ingestão e transformação |
| Machine Learning | Python / scikit-learn e bibliotecas compatíveis | Treinamento e avaliação dos modelos |
| BI | Power BI | Visualização dos indicadores e resultados |
| Versionamento | Git / GitHub | Histórico e colaboração no código |
| CI/CD | GitHub Actions — planejado | Testes e automação das entregas |
| IaC | Terraform — planejado | Definição versionada dos recursos suportados |
| Qualidade | Validações PySpark; pytest planejado | Verificação da integridade dos dados e do código |
| Gestão | Trello | Organização das atividades e acompanhamento das entregas |

### Ambientes de desenvolvimento

O projeto foi inicialmente desenvolvido em um workspace do **Azure Databricks**, com armazenamento ADLS Gen2. Esse ambiente permitiu validar um piloto de ingestão e armazenamento no padrão Medallion.

Posteriormente, o desenvolvimento principal foi transferido para a **Databricks Free Edition**, facilitando a colaboração e reduzindo a dependência de infraestrutura paga.

O ambiente Azure permanece pausado, podendo ser reutilizado para testes ou homologações futuras.

Na Free Edition, o projeto utiliza o catálogo `workspace`, com schemas `bronze`, `silver` e `gold`. Os arquivos originais ficam em Volumes, enquanto as tabelas Delta são gerenciadas pelo ambiente Databricks, sem necessidade de configurar armazenamento externo ADLS Gen2.

## Estrutura do repositório

```text
mba-novo-caged-data-engineering-free-edition/
│
├── README.md
├── job-settings-novo-caged.json
│
├── docs/
│   ├── dicionario_dados
│   │   ├── dicionario-dados-novo-caged-movimentacao.xlsx
│   │ 
│   └── status_entrega
│   │   ├── arquitetura-pipelines-inep-caged.md
│
├── notebooks/
│   ├── 00_setup/
│   │   ├── 01_create_catolog_schema.ipynb
│   │   └── 02_commom_functions.py
│   │
│   ├── 01_ingestao/
│   │   ├── 010_verificar_novos_arquivos.ipynb
│   │   ├── 011_landing_to_bronze.ipynb
│   │   └── 012_dicionarios_referencia.ipynb
│   │
│   ├── 02_transformacao/
│   │   ├── 020_bronze_to_silver_caged.ipynb
│   │   ├── 021_analise_qualidade_bronze_caged.ipynb
│   │   └── 022_bronze_to_silver_ref.ipynb
│   │
│   └── 03_analytics/
│       ├── 030_silver_to_gold_caged.ipynb
│       └── EDA.ipynb
│
├── src/
│   └── transformations/
│
├── tests/
│
└── infrastructure/
    └── terraform/
```

Os diretórios `src/transformations`, `tests` e `infrastructure/terraform` possuem arquivos iniciais de preparação, mas ainda não representam implementações completas de módulos reutilizáveis, testes automatizados ou infraestrutura Terraform.

## Desenvolvimento das camadas de dados

### Landing — Ingestão dos arquivos originais

A Landing utiliza um volume do Unity Catalog:

`/Volumes/workspace/bronze/raw_novo_caged`

Os arquivos oficiais do Novo Caged são recebidos no formato `.7z`, organizados por ano e competência.

O notebook `010_verificar_novos_arquivos.ipynb` consulta o FTP público, identifica novas competências e registra as informações para o processamento posterior.

O fluxo desenvolvido contempla a identificação e o download de novas competências do ano vigente. Revisões retroativas de arquivos já ingeridos exigem uma estratégia complementar.

### Bronze — Preservação e rastreabilidade

A tabela principal é:

`workspace.bronze.novo_caged_movimentacoes`

O notebook `011_landing_to_bronze.ipynb` realiza a extração dos arquivos, a leitura com Apache Spark, a inclusão de metadados de ingestão e a gravação em Delta Lake.

A estrutura permite processamento por competência e sobrescrita seletiva dos períodos processados.

Entre os metadados preservados estão:

- Competência de referência.
- Nome do arquivo de origem.
- Caminho do arquivo original.
- Data e horário de ingestão.

O notebook `012_dicionarios_referencia.ipynb` também disponibiliza na Bronze os dicionários oficiais do Novo Caged, preservando os códigos e as descrições fornecidos pela fonte.

**Decisão arquitetural:** as referências são inicialmente armazenadas na Bronze porque suas descrições e representações podem exigir tratamento e padronização antes do uso em camadas analíticas.

### Silver — Padronização e qualidade

A Silver contempla a tabela:

`workspace.silver.novo_caged_movimentacoes`

O notebook `021_analise_qualidade_bronze_caged.ipynb` documenta análises de qualidade, incluindo valores ausentes, formatos numéricos, domínios categóricos, códigos sem correspondência, duplicidades e cobertura temporal.

O notebook `020_bronze_to_silver_caged.ipynb` implementa:

- Conversão de tipos numéricos e datas.
- Padronização dos nomes das colunas.
- Normalização de formatos numéricos.
- Enriquecimento com descrições de referências.
- Preservação dos metadados de rastreabilidade.
- Reprocessamento seletivo por competência.

O notebook `022_bronze_to_silver_ref.ipynb` trata e disponibiliza dez tabelas de referência tipadas em `workspace.silver`.

#### Decisões de qualidade

**Preservação de duplicidades:** registros com atributos idênticos não são removidos automaticamente, pois a fonte não disponibiliza uma chave natural que permita distinguir com segurança duplicação indevida de movimentações legítimas.

**Códigos sem correspondência:** movimentações com códigos não encontrados nos dicionários são preservadas; suas descrições podem permanecer nulas.

**Valores ausentes:** campos numéricos são convertidos com tratamento explícito de formatos inválidos, evitando exclusões silenciosas.

**Granularidade:** os registros de movimentação permanecem individualizados na Silver; a agregação temporal é responsabilidade da Gold.

#### Cobertura histórica documentada

A análise registrada nos notebooks apresenta:

| Indicador | Resultado documentado |
|---|---|
| Primeiro período | Janeiro de 2021 |
| Último período | Agosto de 2026 |
| Competências | 68 |
| Movimentações | 259.514.177 |

Esses números são provenientes da análise registrada no repositório e deverão ser atualizados quando novas competências forem ingeridas ou houver reprocessamento das fontes.

### Gold — Indicadores semestrais

O notebook `030_silver_to_gold_caged.ipynb` implementa a construção da tabela:

`workspace.gold.fato_caged_semestral`

**Granularidade:** ano × semestre × UF × ocupação CBO 2002.

A fato é construída a partir dos movimentos tratados na Silver e apresenta:

- Total de admissões.
- Total de desligamentos.
- Total de movimentações.
- Saldo de empregos.
- Identificação temporal.
- Código e descrição da UF.
- Código e descrição da ocupação CBO.

As admissões são identificadas por `saldo_movimentacao = 1`, enquanto os desligamentos utilizam `saldo_movimentacao = -1`.

O processamento considera somente semestres com seis competências mensais disponíveis, verificadas globalmente na Silver.

O notebook também implementa validações de unicidade, consistência das métricas e reconciliação dos totais com a Silver, além de recomputação e substituição da tabela Delta para permitir reexecuções sem duplicar os resultados.

**Status:** notebook desenvolvido e versionado; as evidências finais de execução e homologação no workspace devem ser confirmadas.

#### Decisões metodológicas para a Gold

- A análise trabalhista será inicialmente semestral para permitir futura compatibilização com a base de educação formal.
- A fato Caged será construída independentemente da fonte educacional.
- Não serão utilizados indicadores salariais no escopo analítico atual.
- Semestres incompletos serão excluídos da fato definitiva.
- A Silver continuará disponível na granularidade original, permitindo estudos mensais posteriores.

## Integração com educação formal

A proposta do projeto contempla relacionar os indicadores do mercado de trabalho à disponibilidade e à formação de profissionais no Brasil.

A base educacional considerada possui periodicidade semestral. Entretanto, seus campos, classificações e granularidade geográfica ainda precisam ser documentados antes da integração.

Um desafio metodológico é relacionar classificações de cursos ou áreas de formação às ocupações da **Classificação Brasileira de Ocupações (CBO)**.

Essa correspondência não deve ser presumida como direta: uma formação pode estar associada a várias ocupações, e uma ocupação pode reunir profissionais de diferentes formações.

A integração exigirá uma regra de correspondência justificada, possivelmente utilizando grupos ou famílias ocupacionais, evitando multiplicações indevidas nas medidas agregadas.

## Modelagem dimensional e Wide Table

A arquitetura Gold deverá contemplar dois produtos analíticos complementares:

**Modelo dimensional (Star Schema):** organização das fatos e dimensões para análise histórica de admissões, desligamentos, ocupações, regiões e indicadores educacionais.

**Wide Table para Machine Learning:** consolidação das variáveis necessárias à previsão, respeitando a compatibilidade entre granularidades e a disponibilidade temporal das fontes.

A proposta atual considera a previsão de admissões para um semestre futuro, utilizando indicadores históricos de emprego e educação. A definição final das variáveis explicativas, do horizonte de previsão e da granularidade ocupacional será realizada em conjunto com a equipe responsável pelo Machine Learning.

Para evitar *data leakage*, cada observação deverá utilizar apenas informações disponíveis no momento em que a previsão seria realizada.

## Orquestração e automação

O repositório contém o arquivo `job-settings-novo-caged.json`, que descreve um fluxo de tarefas para identificação de novos arquivos, ingestão e transformação dos dados.

A configuração está versionada, porém seus caminhos de notebooks precisam ser revisados para refletir a organização atual do repositório, e sua execução operacional deve ser validada no workspace.

### CI/CD e infraestrutura como código

A implementação de testes automatizados, pipelines GitHub Actions e infraestrutura como código está planejada.

As próximas atividades incluem:

- Extração de regras de transformação reutilizáveis.
- Testes automatizados de qualidade e integridade.
- Integração contínua com GitHub Actions.
- Avaliação de Databricks Declarative Automation Bundles.
- Definição de recursos de infraestrutura por Terraform, respeitando as limitações da Free Edition.

## Limitações e próximos passos

As principais atividades pendentes são:

1. Homologar a fato Gold semestral e documentar os resultados das validações.
2. Revisar a estratégia incremental para identificar alterações em competências já ingeridas, inclusive quando suas contagens não mudarem.
3. Atualizar e validar a configuração dos Databricks Jobs.
4. Receber e analisar a estrutura da base de educação formal (Em desenvolvimento).
5. Definir a correspondência entre cursos, áreas de formação e ocupações (Já realizados).
6. Implementar o modelo dimensional e a Wide Table.
7. Desenvolver, treinar e avaliar os modelos preditivos.
8. Construir as visualizações e o dashboard.
9. Implementar testes automatizados, CI/CD e IaC.
10. Documentar como os requisitos de arquitetura Lambda e streaming serão atendidos ou demonstrados no escopo acadêmico.

### Limitações metodológicas

O Novo Caged representa movimentações de vínculos formais de trabalho. Portanto, o volume de admissões não deve ser interpretado como a totalidade das vagas disponíveis nem como uma medida direta de demanda por competências específicas.

A relação entre formação educacional e ocupação profissional também requer interpretação cuidadosa, considerando classificações distintas, defasagens temporais e ausência de correspondência individual entre bases.

---

**Projeto acadêmico — MBA em Engenharia de Dados | Universidade Presbiteriana Mackenzie.**
