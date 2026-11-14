# Glossário de Dados — Novo CAGED & Censo da Educação Superior (INEP)

**Catálogo:** `workspace` · 

**Escopo:** tabelas do Novo Caged e do Censo da Educação Superior do INEP nas camadas `bronze`, `silver` e `gold`, incluindo a ponte CINE × CBO e as tabelas de Machine Learning.

**Fontes oficiais:**

- Novo CAGED — Cadastro Geral de Empregados e Desempregados (Ministério do Trabalho e Emprego): <https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/novo-caged/meses-anteriores>
- Censo da Educação Superior (INEP): <https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior>

## Arquitetura

| Camada | Papel | Convenção |
| --- | --- | --- |
| `bronze` | Dados brutos, exatamente como extraídos da fonte | Todas as colunas como STRING; metadados de ingestão com prefixo `_` |
| `silver` | Dados limpos e tipados | Códigos convertidos para tipos numéricos/datas; descrições enriquecidas via de-para com os dicionários `ref_*` (colunas `*_descricao`) |
| `gold` | Modelo dimensional e tabelas analíticas de ML prontas para consumo | Fatos (`fato_*`), dimensões (`dim_*`), bridges (`bridge_*`) e tabelas de ML (`ml_*`, `previsoes_*` e análises), com colunas de auditoria (`dt_processamento`, `versao_transformacao`) |

**Fluxo CAGED:** `bronze.novo_caged_movimentacoes` → `silver.novo_caged_movimentacoes` → `gold.fato_caged_semestral` (via `silver.novo_caged_movimentacoes_semestral`)

**Fluxo INEP:** `bronze.inep_superior_cursos` → `silver.inep_superior_cursos` → `gold.fato_inep_educacao_brasil_anual` / `gold.fato_inep_educacao_uf_anual`

**Fluxo ML (Wide Table → previsões):** `silver.novo_caged_movimentacoes` + fatos INEP (cruzadas via `bridge_cine_cbo_provisoria`) → `gold.ml_features_mensal_uf_cbo` → triagem de features (`ml_features_ols_screening`) → validação (`ml_backtest_admissoes`) → `gold.previsoes_admissoes` → análise de desalinhamento (`desalinhamento_formacao_mercado`)

---

# Contexto de negócios das fontes

## Novo CAGED (Ministério do Trabalho e Emprego)

**O que é:** O CAGED é o registro administrativo das admissões e desligamentos do emprego formal brasileiro (regime CLT, rural, aprendiz e servidor público estatutário não-celetista excluído conforme categoria). A partir de 2020 o MTE migrou para o **Novo CAGED**, alimentado pelo eSocial/CAGED Digital, que substituiu o CAGED legado (baseado em PIS/PASEP) — os microdados mensais usados neste projeto seguem o layout do Novo CAGED (competências a partir de jan/2021).

**Para que serve (usos oficiais):**

* Base das **estatísticas oficiais do mercado de trabalho** do governo: estoque de emprego, admissões, desligamentos e saldo líquido por mês, UF, setor e ocupação.
* Insumo para **políticas públicas de trabalho e renda**: dimensionamento do seguro-desemprego, abono salarial, programas de primeira oportunidade e de proteção ao emprego.
* Referência para **análises setoriais** via CNAE (seção/subclasse) e **ocupacionais** via CBO 2002, incluindo debate sobre demanda por qualificação.

**Limitações de leitura:**

* Cobrem somente **emprego formal** — não capturam informalidade, MEI (com limites), trabalho por conta própria ou desemprego.
* Cada linha é uma **movimentação** (admissão ou desligamento), não um trabalhador: uma mesma pessoa pode aparecer mais de uma vez no período.
* O **saldo da movimentação** (+1/-1) é o sinal analítico básico: agregado, produz o saldo líquido de vagas por recorte (é o que a `fato_caged_semestral` materializa por ano × semestre × UF × CBO).
* Semestres com menos de 6 meses de competência são **parciais** (ex.: 2026S2 com jul–ago) e não entram na fato gold.

**Contextos relevantes às colunas do projeto:**

* `ind_trab_intermitente` / `ind_trab_parcial` e `indicador_aprendiz` refletem a Reforma Trabalhista (Lei 13.467/2017), que formalizou o contrato intermitente, o parcial e o de aprendizagem — recortes úteis para precarização/primeiro emprego.
* `tipomovimentação` distingue **motivos** de desligamento (sem justa causa, pedido, fim de contrato, morte, transferência etc.), permitindo análises de rotatividade além do simples volume.
* `graudeinstrução` e `raçacor` permitem recortes de qualificação e diversidade no mercado formal — ponte natural com os dados do Censo INEP.
* `mediana_salario_admissao` (na tabela semestral) aproxima o salário de entrada típico por período, evitando distorções de outliers.

## Censo da Educação Superior (INEP)

**O que é:** Levantamento censitário **anual e obrigatório** de todas as IES e cursos de graduação do Brasil (presenciais e EAD, públicas e privadas). É o instrumento oficial de estatística da educação superior e existe em formato comparável desde meados dos anos 1990. Cada curso responde ao Censo no ano de referência (`NU_ANO_CENSO`); os microdados por curso alimentam as camadas bronze/silver/gold deste projeto.

**Para que serve (usos oficiais):**

* Base para **regulação do MEC/SINAES**: autorização, reconhecimento e renovação de cursos, além de indicadores de qualidade (ENADE, CPC, IGC).
* Insumo para **política educacional**: dimensionamento da expansão de vagas, EAD, interiorização, gratuidade e financiamento estudantil.
* Fonte de referência para **pesquisa acadêmica e mercado educacional**: demanda (inscritos), acesso (ingressantes), cobertura (matrículas) e conclusão.

**Ciclo analítico do aluno (espelha os prefixos `QT_*` da bronze):**

`vagas` (`QT_VG_*`) → `inscritos` (`QT_INSC*`) → `ingressantes` (`QT_ING_*`) → `matrículas` (`QT_MAT_*`) → `concluintes` (`QT_CONC_*`), com recortes demográficos (sexo, faixa etária, raça/cor, nacionalidade, deficiência) e socioeconômicos (financiamento, reserva de vagas, origem escolar). Os estados intermediários (`QT_SIT_*`: trancado, desvinculado, transferido, falecido) explicam a evasão.

**Contextos relevantes às colunas do projeto:**

* **Classificação CINE Brasil** (`CO_/NO_CINE_*`): adotada pelo INEP a partir do Censo 2019 para alinhar os cursos à classificação internacional CINE/ISCED 2013 da UNESCO, garantindo comparabilidade internacional — é a hierarquia em 4 níveis da `dim_cine_brasil` (área geral → específica → detalhada → rótulo).
* **Reserva de vagas** (`QT_*_RV*`): implementação da **Lei de Cotas (Lei 12.711/2012)** — escola pública, étnico-racial, PPI, quilombola, refugiado, pessoa com deficiência, idoso etc. — permitindo medir efetividade das políticas de inclusão.
* **Financiamento** (`QT_*_FINANC*`, `FIES`, `PROUNI*`, `RPFIES`): medem a dependência das matrículas a crédito estudantil (FIES) e bolsa (Prouni) — proxy clássica de renda do aluno.
* **Modalidade EAD** (`TP_MODALIDADE_ENSINO`): recorte central desde a explosão do ensino a distância nos anos 2010 — na `fato_inep_educacao_uf_anual` as métricas de vagas são restritas a cursos presenciais para evitar distorção da oferta por UF (aluno EAD não se concentra na UF da sede).
* **`tipo_dimensao` / `TP_DIMENSAO`**: distingue a unidade de observação do Censo (matrícula vs curso), importante ao agregar `quantidade_cursos`.
* `ano_censo_edicao` (na `dim_cine_brasil`) preserva a edição do Censo de onde veio a nomenclatura vigente, já que nomes de rótulos CINE mudam entre censos.

## Cruzamento CAGED × INEP (proposta analítica do projeto)

O projeto conecta **oferta educacional** (Censo INEP: ingressantes/concluintes por área CINE) com **demanda do mercado formal** (CAGED: admissões/desligamentos por ocupação CBO). Análises típicas:

* Comparar a evolução de concluintes em uma área CINE com o saldo de admissões em ocupações relacionadas (aproximação de **alinhamento formação × mercado de trabalho**).
* Usar salário mediano de admissão (CAGED) como retorno médio ao mercado formal por ocupação, contrastando entre áreas de formação.
* Recortes por UF para identificar desequilíbrios regionais de oferta/absorção.

> Na camada gold, a ponte CINE × CBO é materializada — em versão provisória, curada pela equipe e pendente de correspondência oficial do MEC — pelas tabelas `bridge_cine_cbo_provisoria` e `bridge_cine_cbo_provisoria_cobertura` (seções 3.6 e 3.7).

## Verificação dos contextos com os dados (executada em 31/10/2026)

As afirmações abaixo foram confrontadas com os dados reais das tabelas (o texto das páginas oficiais do MTE/INEP não pôde ser varrido nesta sessão — compute SQL-only, sem acesso web — mas os registros confirmam a consistência dos contextos):

| Afirmação | Verificado em | Resultado |
| --- | --- | --- |
| CAGED cobre jan/2021–ago/2026 | `silver.novo_caged_movimentacoes` | ✅ `competencia_mov` de 2021-01-01 a 2026-08-01 |
| 2026S2 é parcial (só jul–ago) | `silver.novo_caged_movimentacoes_semestral` | ✅ `meses_cobertos = 2` (único semestre com menos de 6) |
| Fato gold contém apenas semestres completos | `gold.fato_caged_semestral` | ✅ 2026S1 presente, 2026S2 com 0 registros; anos 2021–2026 |
| De-para CBO com código de 6 dígitos (zero à esquerda) | `gold.dim_cbo_ocupacao` | ✅ ex.: `'251205'` (Economista) gravado como STRING |
| Hierarquia CINE populada nos 4 níveis | `gold.dim_cine_brasil` | ✅ 11 áreas gerais e 372 rótulos distintos |
| Censo INEP no projeto cobre 2021–2024 | `silver.inep_superior_cursos` | ✅ `ano_censo` de 2021 a 2024 |
| Saldo pode ser negativo no grão da fato | `gold.fato_caged_semestral` | ✅ mín. observado: -15.098 (UF×CBO com mais desligamentos) |

**Insight incidental da validação:** a mediana salarial de admissão subiu de R$ 1.386,87 (2021S1) para R$ 2.000,00 (2026S2) e a mediana de idade de 30 para 31 anos — coerente com o contexto de recuperação do mercado formal pós-pandemia.

---

# 1. Camada BRONZE — dados brutos

## 1.1 `workspace.bronze.novo_caged_movimentacoes`

**Descrição:** Movimentações mensais de admissão e desligamento do Novo CAGED, extraídas dos arquivos públicos mensais do MTE (layout original do arquivo `.txt`). Grão: uma linha por movimentação (vínculo admitido/desligado). Todas as colunas são STRING, preservando o arquivo original.

| Coluna | Descrição |
| --- | --- |
| `competênciamov` | Competência da movimentação (mês de referência, MMAAAA) |
| `região` | Código da região |
| `uf` | Código da UF |
| `município` | Código do município |
| `seção` | Código da seção CNAE |
| `subclasse` | Código da subclasse CNAE |
| `saldomovimentação` | Saldo da movimentação (1 = admissão, -1 = desligamento) |
| `cbo2002ocupação` | Código CBO 2002 da ocupação |
| `categoria` | Código da categoria do trabalhador |
| `graudeinstrução` | Código do grau de instrução |
| `idade` | Idade do trabalhador |
| `horascontratuais` | Horas contratuais |
| `raçacor` | Código de raça/cor |
| `sexo` | Código do sexo |
| `tipoempregador` | Código do tipo de empregador |
| `tipoestabelecimento` | Código do tipo de estabelecimento |
| `tipomovimentação` | Código do tipo de movimentação (admissão/desligamento e motivos) |
| `tipodedeficiência` | Código do tipo de deficiência |
| `indtrabintermitente` | Indicador de trabalho intermitente |
| `indtrabparcial` | Indicador de trabalho parcial |
| `salário` | Salário da movimentação |
| `tamestabjan` | Tamanho do estabelecimento em janeiro (faixa de vínculos) |
| `indicadoraprendiz` | Indicador de aprendiz |
| `origemdainformação` | Origem da informação |
| `competênciadec` | Competência declarada (data de declaração do movimento) |
| `indicadordeforadoprazo` | Indicador de envio fora do prazo |
| `unidadesaláriocódigo` | Código da unidade do salário (mensal/hora etc.) |
| `valorsaláriofixo` | Valor do salário fixo |
| `_competencia_referencia` | Competência de referência do arquivo processado |
| `_arquivo_origem` | Nome do arquivo de origem |
| `_caminho_origem` | Caminho do arquivo de origem |
| `_data_ingestao` | Data/hora da ingestão na bronze |

## 1.2 `workspace.bronze.inep_superior_cursos`

**Descrição:** Microdados do Censo da Educação Superior (INEP), tabela de cursos — uma linha por curso de graduação por ano do Censo. Nomes originais do dicionário INEP (tudo STRING). Cerca de 200 colunas, organizadas em famílias:

| Família de colunas | Descrição |
| --- | --- |
| Identificação temporal/espacial | `NU_ANO_CENSO`, `NO_REGIAO`/`CO_REGIAO`, `NO_UF`/`SG_UF`/`CO_UF`, `NO_MUNICIPIO`/`CO_MUNICIPIO`, `IN_CAPITAL` |
| Instituição | `CO_IES`, `TP_ORGANIZACAO_ACADEMICA`, `TP_CATEGORIA_ADMINISTRATIVA`, `TP_REDE`, `IN_COMUNITARIA`, `IN_CONFESSIONAL` |
| Curso | `NO_CURSO`/`CO_CURSO`, `TP_DIMENSAO`, `TP_GRAU_ACADEMICO`, `TP_NIVEL_ACADEMICO`, `TP_MODALIDADE_ENSINO`, `IN_GRATUITO` |
| Classificação CINE Brasil | `NO_CINE_ROTULO`/`CO_CINE_ROTULO`/`CO_CINE_ROTULO2`, e pares código/nome de área geral, específica e detalhada (`CO_/NO_CINE_AREA_*`) |
| Vagas (prefixo `QT_VG_*`) | Vagas ofertadas: total, diurno, noturno, EAD, novas, processo seletivo, remanescentes, programas especiais |
| Inscritos (prefixo `QT_INSC*`) | Inscritos no processo seletivo: total e por tipo de vaga |
| Ingressantes (prefixo `QT_ING_*`) | Ingressantes por: sexo, turno, tipo de seleção (vestibular, ENEM, avaliação seriada, etc.), faixa etária (`0_17` a `60_MAIS`), raça/cor (`BRANCA`, `PRETA`, `PARDA`, `AMARELA`, `INDIGENA`, `CORND`), nacionalidade (`NACBRAS`/`NACESTRANG`), deficiência, financiamento (`FINANC`, `FIES`, `PROUNII/P`, etc.), reserva de vagas (`RV*`: escola pública, étnico, PPI, quilombola, refugiado, etc.), origem escolar (`PROCESCPUBLICA`/`PROESCPRIVADA`), PARFOR, apoio social, atividade extracurricular, mobilidade acadêmica |
| Matrículas (prefixo `QT_MAT_*`) | Matrículas ativas, mesmos recortes dos ingressantes (sexo, turno, faixa etária, raça/cor, nacionalidade, deficiência, financiamento, reserva de vagas, etc.) |
| Concluintes (prefixo `QT_CONC_*`) | Concluintes, mesmos recortes dos ingressantes |
| Situação do curso | `QT_SIT_TRANCADA`, `QT_SIT_DESVINCULADO`, `QT_SIT_TRANSFERIDO`, `QT_SIT_FALECIDO`, `QT_ALUNO_DEFICIENTE`, `QT_CURSO` |
| Metadados de ingestão | `arquivo_origem`, `ano_ingestao`, `hash_origem`, `dt_ingestao` |

> **Convenção INEP:** `QT_ING_*` = ingressantes, `QT_MAT_*` = matrículas, `QT_CONC_*` = concluintes. Ex.: `QT_MAT_18_24` = matrículas de 18 a 24 anos; `QT_CONC_PARDA` = concluintes autodeclarados pardos.

## 1.3 Dicionários de referência `ref_*` (10 tabelas)

**Descrição:** Tabelas de-para (código → descrição) do layout oficial do Novo CAGED. Na bronze, todas com colunas `codigo` (STRING) e `descricao` (STRING). São a base do enriquecimento da camada silver.

| Tabela | Conteúdo |
| --- | --- |
| `bronze.ref_categoria` | Categorias de trabalhador |
| `bronze.ref_cbo_ocupacao` | Ocupações CBO 2002 |
| `bronze.ref_grau_instrucao` | Graus de instrução |
| `bronze.ref_municipio` | Municípios |
| `bronze.ref_regiao` | Regiões geográficas |
| `bronze.ref_secao` | Seções CNAE |
| `bronze.ref_subclasse` | Subclasses CNAE |
| `bronze.ref_tipo_estabelecimento` | Tipos de estabelecimento |
| `bronze.ref_tipo_movimentacao` | Tipos de movimentação |
| `bronze.ref_uf` | Unidades da Federação |

---

# 2. Camada SILVER — dados limpos e enriquecidos

## 2.1 `workspace.silver.novo_caged_movimentacoes`

**Descrição:** Movimentações do Novo CAGED tipadas e enriquecidas com descrições (de-para com os dicionários `ref_*`). Grão: uma linha por movimentação. Fonte: `workspace.bronze.novo_caged_movimentacoes`. Clusterizada por `competencia_mov`.

| Grupo | Colunas | Descrição |
| --- | --- |--- |
| Temporal | `competencia_mov` (date), `competencia_dec` (date) | Competência da movimentação e competência declarada |
| Geografia | `regiao` (smallint) + `regiao_descricao`, `uf` (smallint) + `uf_descricao`, `municipio` (int) + `municipio_descricao` | Códigos e nomes de região, UF e município |
| Atividade econômica | `secao` (string) + `secao_descricao`, `subclasse` (int) + `subclasse_descricao` | Seção e subclasse CNAE |
| Ocupação | `cbo2002_ocupacao` (int) + `cbo2002_ocupacao_descricao` | Código CBO 2002 e nome da ocupação |
| Movimentação | `saldo_movimentacao` (smallint: 1 = admissão, -1 = desligamento), `tipo_movimentacao` + `tipo_movimentacao_descricao` | Natureza e motivo do movimento |
| Perfil do trabalhador | `categoria` + `categoria_descricao`, `grau_instrucao` + `grau_instrucao_descricao`, `idade` (smallint), `raca_cor` (smallint), `sexo` (smallint), `tipo_deficiencia` (smallint), `ind_trab_intermitente`, `ind_trab_parcial`, `indicador_aprendiz` | Categoria, escolaridade, idade, raça/cor, sexo, deficiência, indicadores de regime de trabalho |
| Empregador/estabelecimento | `tipo_empregador` (smallint), `tipo_estabelecimento` (smallint) + `tipo_estabelecimento_descricao`, `tam_estab_jan` (smallint) | Tipo de empregador, tipo e porte do estabelecimento |
| Jornada e salário | `horas_contratuais` (decimal(5,2)), `salario` (decimal(18,2)), `unidade_salario_codigo` (smallint), `valor_salario_fixo` (decimal(18,2)) | Horas contratuais, salário da movimentação e salário fixo |
| Qualidade/origem | `origem_informacao`, `indicador_fora_prazo` | Origem da informação e envio fora do prazo |
| Auditoria | `competencia_referencia`, `arquivo_origem`, `caminho_origem`, `data_ingestao` | Rastreabilidade até o arquivo original |

## 2.2 `workspace.silver.novo_caged_movimentacoes_semestral`

**Descrição:** Agregado semestral do Novo CAGED (jan/2021–ago/2026): admissões, desligamentos e saldo por semestre, com meses cobertos e perfil (mediana de salário e idade) das admissões. **Atenção:** 2026S2 é parcial (apenas jul–ago/2026). Fonte: `workspace.silver.novo_caged_movimentacoes`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `semestre` | string | Rótulo do semestre (ex.: `2024S1`) |
| `data_inicio` | date | Primeiro dia do semestre |
| `meses_cobertos` | bigint | Quantidade de meses com dados no semestre |
| `movimentacoes_total` | bigint | Total de movimentações |
| `admissoes` | bigint | Total de admissões |
| `desligamentos` | bigint | Total de desligamentos |
| `saldo` | bigint | Saldo (admissões - desligamentos) |
| `mediana_salario_admissao` | decimal(18,2) | Mediana do salário das admissões |
| `mediana_idade_admissao` | smallint | Mediana da idade das admissões |

## 2.3 `workspace.silver.inep_superior_cursos`

**Descrição:** Cursos do Censo da Educação Superior tipados e agregados por curso. Fonte: `workspace.bronze.inep_superior_cursos`.

| Grupo | Colunas | Descrição |
| --- | --- | --- |
| Temporal/espacial | `ano_censo` (int), `nome_regiao`/`codigo_regiao`, `nome_uf`/`sigla_uf`/`codigo_uf`, `nome_municipio`/`codigo_municipio`, `indicador_capital` | Ano do Censo e localização do curso |
| Instituição/Curso | `tipo_dimensao` (int), `codigo_ies`, `codigo_curso`, `nome_curso`, `tipo_organizacao_academica`, `tipo_categoria_administrativa`, `tipo_rede`, `indicador_gratuito` | Identificação e características da IES e do curso |
| Classificação CINE | `codigo_cine_rotulo` + `nome_cine_rotulo`, `codigo_cine_area_geral` + `nome_cine_area_geral`, `codigo_cine_area_especifica` + `nome_cine_area_especifica`, `codigo_cine_area_detalhada` + `nome_cine_area_detalhada` | Classificação CINE Brasil em 4 níveis |
| Modalidade/Nível | `tipo_modalidade_ensino` (int), `tipo_grau_academico`, `tipo_nivel_academico` | Presencial/EAD, bacharelado/licenciatura/tecnólogo |
| Métricas agregadas | `quantidade_cursos`, `quantidade_vagas`, `quantidade_inscritos`, `quantidade_ingressantes`, `quantidade_matriculas`, `quantidade_concluintes`, `quantidade_desvinculados`, `quantidade_trancamentos` (todas bigint) | Volumetria do curso no ano |
| Auditoria | `arquivo_origem`, `hash_origem`, `dt_ingestao`, `dt_transformacao`, `versao_transformacao` | Rastreabilidade da bronze até a silver |

## 2.4 Dicionários `ref_*` (silver)

**Descrição:** Mesmos dicionários da bronze, agora tipados (`codigo` em tipo numérico adequado, `descricao` string), com comentários de coluna e tabela.

| Tabela | Colunas | Comentário |
| --- | --- | --- |
| `silver.ref_categoria` | `codigo` (smallint), `descricao` | Categorias de trabalhador (dicionário do Novo Caged) |
| `silver.ref_cbo_ocupacao` | `codigo` (int), `descricao` | Ocupações CBO 2002 (dicionário do Novo Caged) |
| `silver.ref_grau_instrucao` | `codigo` (smallint), `descricao` | Graus de instrução (dicionário do Novo Caged) |
| `silver.ref_municipio` | `codigo` (int), `descricao` | Municípios — código IBGE (dicionário do Novo Caged) |
| `silver.ref_regiao` | `codigo` (smallint), `descricao` | Regiões geográficas (dicionário do Novo Caged) |
| `silver.ref_secao` | `codigo` (string), `descricao` | Seções CNAE (dicionário do Novo Caged) |
| `silver.ref_subclasse` | `codigo` (int), `descricao` | Subclasses CNAE (dicionário do Novo Caged) |
| `silver.ref_tipo_estabelecimento` | `codigo` (smallint), `descricao` | Tipos de estabelecimento (dicionário do Novo Caged) |
| `silver.ref_tipo_movimentacao` | `codigo` (smallint), `descricao` | Tipos de movimentação (dicionário do Novo Caged) |
| `silver.ref_uf` | `codigo` (smallint), `descricao` | Unidades da Federação (dicionário do Novo Caged) |

---

# 3. Camada GOLD — modelo dimensional e Machine Learning

## 3.1 `workspace.gold.dim_cbo_ocupacao`

**Descrição:** Dimensão de ocupações. Grão: um registro por código CBO 2002. Fonte: dicionário CBO 2002 do Novo CAGED.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `codigo_cbo` | string | Chave da dimensão: código CBO 2002 com 6 dígitos (zero à esquerda) |
| `nome_ocupacao` | string | Descrição da ocupação no dicionário CBO 2002 |
| `dt_processamento` | timestamp | Data e hora da gravação da dimensão |
| `versao_transformacao` | string | Versão da transformação que produziu a dimensão |

## 3.2 `workspace.gold.dim_cine_brasil`

**Descrição:** Dimensão da classificação CINE Brasil em quatro níveis (área geral → específica → detalhada → rótulo). Grão: um registro por rótulo CINE. A nomenclatura usada é a da edição mais recente do Censo.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `codigo_cine_area_geral` / `nome_cine_area_geral` | string | Área geral CINE |
| `codigo_cine_area_especifica` / `nome_cine_area_especifica` | string | Área específica CINE |
| `codigo_cine_area_detalhada` / `nome_cine_area_detalhada` | string | Área detalhada CINE |
| `codigo_cine_rotulo` | string | Chave da dimensão: código CINE do rótulo (grão) |
| `nome_cine_rotulo` | string | Nome do rótulo (nomenclatura da edição mais recente) |
| `ano_censo_edicao` | int | Ano do Censo de onde a nomenclatura vigente foi extraída |
| `dt_processamento` | timestamp | Data e hora da gravação da dimensão |
| `versao_transformacao` | string | Versão da transformação que produziu a dimensão |

## 3.3 `workspace.gold.fato_caged_semestral`

**Descrição:** Fato semestral do Novo CAGED. **Grão: ano × semestre × UF × CBO 2002.** Fonte: `workspace.silver.novo_caged_movimentacoes`. Somente semestres completos (6 meses); sem dados salariais. Construída pelo notebook `030_silver_to_gold_caged`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `ano` | int | Ano da movimentação |
| `semestre` | int | Semestre (1 ou 2) |
| `uf` | smallint | Código da UF |
| `cbo2002_ocupacao` | int | Código CBO 2002 da ocupação |
| `uf_descricao` | string | Nome da UF (de-para `silver.ref_uf`) |
| `cbo2002_ocupacao_descricao` | string | Nome da ocupação (de-para `silver.ref_cbo_ocupacao`) |
| `admissoes` | bigint | Total de admissões no grão |
| `desligamentos` | bigint | Total de desligamentos no grão |
| `total_movimentacoes` | bigint | Total de movimentações |
| `saldo` | bigint | Saldo (admissões - desligamentos) |

## 3.4 `workspace.gold.fato_inep_educacao_brasil_anual`

**Descrição:** Fato anual da educação superior para o **Brasil**. Grão: ano × rótulo CINE × modalidade de ensino. Fonte: `workspace.silver.inep_superior_cursos`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `ano_censo` | int | Ano do Censo |
| `codigo_cine_rotulo` / `nome_cine_rotulo` | string | Rótulo CINE do curso |
| `codigo_cine_area_geral` / `nome_cine_area_geral` | string | Área geral CINE |
| `codigo_cine_area_especifica` / `nome_cine_area_especifica` | string | Área específica CINE |
| `codigo_cine_area_detalhada` / `nome_cine_area_detalhada` | string | Área detalhada CINE |
| `tipo_modalidade_ensino` | int | Modalidade (presencial/EAD) |
| `ingressantes`, `matriculas`, `concluintes`, `cursos`, `vagas`, `inscritos` | bigint | Métricas agregadas por curso |
| `hash_silver_origem`, `versao_silver_origem`, `registros_silver_origem` | string/int | Auditoria da origem em silver |
| `versao_transformacao`, `dt_processamento` | string/timestamp | Auditoria da carga em gold |

## 3.5 `workspace.gold.fato_inep_educacao_uf_anual`

**Descrição:** Fato anual da educação superior **por UF**. Grão: ano × UF × rótulo CINE × modalidade de ensino (somente cursos presenciais nas métricas de vagas). Fonte: `workspace.silver.inep_superior_cursos`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `ano_censo` | int | Ano do Censo |
| `sigla_uf` | string | Sigla da UF |
| `codigo_cine_rotulo` / `nome_cine_rotulo` | string | Rótulo CINE do curso |
| `codigo_cine_area_geral` / `nome_cine_area_geral` | string | Área geral CINE |
| `codigo_cine_area_especifica` / `nome_cine_area_especifica` | string | Área específica CINE |
| `codigo_cine_area_detalhada` / `nome_cine_area_detalhada` | string | Área detalhada CINE |
| `tipo_modalidade_ensino` | int | Modalidade (presencial/EAD) |
| `ingressantes`, `matriculas`, `concluintes` | bigint | Métricas de alunos por UF |
| `cursos_presenciais`, `vagas_presenciais`, `inscritos_presenciais` | bigint | Métricas restritas a cursos presenciais |
| `hash_silver_origem`, `versao_silver_origem`, `registros_silver_origem` | string/int | Auditoria da origem em silver |
| `versao_transformacao`, `dt_processamento` | string/timestamp | Auditoria da carga em gold |

## 3.6 `workspace.gold.bridge_cine_cbo_provisoria`

**Descrição:** Bridge (tabela de correspondência) entre a oferta educacional e o mercado formal: liga a **área específica CINE** (lado educação) ao **subgrupo principal CBO 2002** (lado ocupação). Grão: um registro por par área específica × subgrupo CBO. **Versão provisória**: mapeamento curado pela equipe (notebooks `032_mapeamento_cine_cbo` e `033_construcao_bridge_cine_cbo`), sem fonte oficial — `aprovado_oficial` é sempre `false` até existir correspondência oficial do MEC.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `codigo_cine_area_geral` / `nome_cine_area_geral` | string | Área geral CINE (contexto do par) |
| `codigo_cine_area_especifica` / `nome_cine_area_especifica` | string | Chave do lado CINE: código de 3 dígitos da área específica |
| `codigo_cbo_subgrupo` | string | Chave do lado CBO: subgrupo principal CBO (3 dígitos — dígitos 2 a 4 do código CBO 2002) |
| `codigo_cbo_grande_grupo` | string | Grande grupo CBO (1º dígito, contexto) |
| `exemplo_ocupacao` | string | Ocupação representativa do subgrupo (apenas ilustrativa) |
| `tipo_mapeamento` | string | Sempre APROXIMADO nesta tabela — versão provisória sem fonte oficial |
| `nivel_mapeamento` | string | Grão do par: `AREA_ESPECIFICA_X_SUBGRUPO_PRINCIPAL` |
| `confianca` | string | Confiança do par: ALTA, MEDIA ou BAIXA |
| `justificativa` | string | Justificativa textual do par, para auditoria |
| `fonte_mapeamento` | string | Fonte do mapeamento (curada pela equipe, não oficial) |
| `aprovado_oficial` | boolean | Sempre false — aguarda correspondência oficial do MEC |
| `versao_mapeamento` | string | Versão do mapeamento provisório |
| `dt_processamento` | timestamp | Data e hora da gravação |
| `versao_transformacao` | string | Versão da transformação |

## 3.7 `workspace.gold.bridge_cine_cbo_provisoria_cobertura`

**Descrição:** Diagnóstico de cobertura do mapeamento provisório: para cada área específica CINE, quantos pares CBO foram mapeados e quais ficaram de fora (com motivo). Complementa a `bridge_cine_cbo_provisoria` na auditoria do cruzamento CINE × CBO. Grão: um registro por área específica × versão do mapeamento.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `codigo_cine_area_especifica` / `nome_cine_area_especifica` | string | Área específica CINE diagnosticada |
| `posicao` | string | Situação da área no mapeamento (dentro/fora) |
| `qtd_pares_cbo` | bigint | Quantidade de pares CBO mapeados para a área |
| `motivo_fora` | string | Motivo pelo qual a área ficou fora do mapeamento (quando aplicável) |
| `versao_mapeamento` | string | Versão do mapeamento diagnosticado |
| `dt_processamento` | timestamp | Data e hora da gravação |

## 3.8 `workspace.gold.ml_features_mensal_uf_cbo`

**Descrição:** Wide Table (tabela de features) para Machine Learning — a consolidação mensal prevista na arquitetura. Grão: **competência (mês) × UF × subgrupo principal CBO (3 dígitos)**, cobrindo somente subgrupos presentes na bridge. Variável-alvo: `admissoes` (admissões do mês). Cobertura: jan/2021–ago/2026. Features educacionais defasadas 1 a 5 anos (def1–def5) para respeitar o tempo de formação e evitar *data leakage*. Construída pelo notebook `035_gold_ml_features`.

| Família | Colunas | Descrição |
| --- | --- | --- |
| Chaves | `competencia_mov` (date), `sigla_uf` (string), `codigo_cbo_subgrupo` (string) | Grão da observação |
| Alvo/contexto | `admissoes`, `desligamentos` (bigint) | **ALVO** é `admissoes`; desligamentos como contexto |
| Autoregressivas | `admissoes_lag_1/3/12`, `admissoes_ma_3/12`, `desligamentos_lag_1`, `desligamentos_ma_3`, `saldo_lag_1`, `salario_mediano_lag_1` | Lags e médias móveis de meses anteriores (sem o mês corrente) |
| Escala log | `admissoes_log_lag_1`, `admissoes_log_ma_3`, `admissoes_log_ma_12` | log1p das variáveis autoregressivas |
| Sazonalidade | `mes_sin`, `mes_cos` | Codificação cíclica do mês do ano |
| Educacionais (via bridge) | `concluintes_def1/def2/def3`, `matriculas_def1`, `ingressantes_def3`, `ingressantes_def5`, `share_ead_def1`, `razao_contratacao_matricula` | Métricas do Censo INEP defasadas (1–5 anos) e razão contratação/matrícula |
| Auditoria | `versao_transformacao`, `versao_bridge_origem`, `dt_processamento` | Rastreabilidade, incluindo a versão da bridge usada no de-para |

## 3.9 `workspace.gold.ml_features_ols_screening`

**Descrição:** Triagem estatística das features candidatas da Wide Table via regressão OLS *pooled* com efeitos fixos de UF e mês. Grão: uma linha por feature avaliada. Suporta a decisão de quais variáveis entram no modelo final. Também produzida pelo notebook `035_gold_ml_features`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `feature` | string | Feature candidata avaliada |
| `coeficiente` | double | Coeficiente OLS (pooled, efeitos fixos UF e mês) |
| `erro_padrao` / `estatistica_t` / `p_valor` | double | Significância do coeficiente |
| `vif` | double | Variance Inflation Factor (multicolinearidade) |
| `decisao_screening` / `criterio` | string | Veredito da triagem e critério aplicado |
| `r2_ajustado` | double | R² ajustado do modelo de screening |
| `n_observacoes` | bigint | Observações do modelo |
| `versao_transformacao` / `dt_processamento` | string/timestamp | Versão do snapshot avaliado e data da gravação |

## 3.10 `workspace.gold.ml_backtest_admissoes`

**Descrição:** Métricas de backtest dos modelos preditivos, com validação por cutoffs móveis (jan–dez/2025). Grão: nível × escopo × modelo × cutoff. O nível `GERAL` agrega o holdout (`competencia_mov` nula); `FOLD` traz a métrica de um cutoff. O escopo separa `TODAS_SERIES` (todas as UF×subgrupo) de `AMOSTRA_SARIMAX` (amostra avaliada também com SARIMAX). Construída pelo notebook `036_treino_backtest_admissoes`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `nivel` | string | `GERAL` (holdout agregado) ou `FOLD` (cutoff específico) |
| `escopo` | string | `TODAS_SERIES` ou `AMOSTRA_SARIMAX` |
| `modelo` | string | Modelo avaliado |
| `competencia_mov` | date | Cutoff do fold (nulo no nível `GERAL`) |
| `n` | bigint | Observações avaliadas |
| `mae`, `rmse`, `smape`, `mase` | double | Métricas de erro |
| `versao_backtest` / `versao_features` | string | Versões do backtest e da Wide Table usada |
| `dt_processamento` | timestamp | Data/hora da gravação |

## 3.11 `workspace.gold.previsoes_admissoes`

**Descrição:** Previsões de admissões por UF × subgrupo CBO para horizontes futuros (set/2026–ago/2027), geradas a partir do último mês real disponível (ago/2026). Grão: UF × subgrupo CBO × competência prevista × modelo. `previsao_admissoes` é o valor pós-ajuste e `previsao_bruta` o valor original do modelo — a diferença indica calibração aplicada. Construída pelo notebook `037_previsoes_operacionais`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `sigla_uf` / `codigo_cbo_subgrupo` | string | Chaves da série (UF × subgrupo CBO 3 dígitos) |
| `competencia_prevista` | timestamp | Mês previsto (set/2026–ago/2027) |
| `horizonte_h` | bigint | Horizonte da previsão em meses à frente |
| `previsao_admissoes` / `previsao_bruta` | double | Previsão ajustada e bruta |
| `modelo` / `versao_modelo` / `versao_features` / `versao_previsao` | string | Modelo e versões de rastreabilidade |
| `ultimo_mes_real` | timestamp | Último mês real usado como base (ago/2026) |
| `dt_processamento` | timestamp | Data/hora da gravação |

## 3.12 `workspace.gold.desalinhamento_formacao_mercado`

**Descrição:** Análise de desalinhamento entre formação e mercado: compara, por UF × subgrupo CBO, a previsão de admissões dos próximos 12 meses com os concluintes e matrículas do Censo INEP (via bridge CINE × CBO). Materializa a resposta analítica central do projeto — onde a oferta de formação está descolada da demanda prevista do mercado formal. Construída pelo notebook `038_desalinhamento_formacao_mercado`.

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `sigla_uf` / `codigo_cbo_subgrupo` | string | Grão da análise |
| `previsao_admissoes_12m` | double | Admissões previstas nos próximos 12 meses |
| `admissoes_reais_12m` | bigint | Admissões reais dos últimos 12 meses (referência) |
| `concluintes_censo` / `matriculas_censo` | double | Concluintes e matrículas do Censo INEP no recorte (via bridge) |
| `adm_por_concluinte_prev` / `adm_por_concluinte_hist` / `adm_por_matricula_prev` | double | Razões admissões/concluintes (prevista e histórica) e admissões/matrículas |
| `tendencia_razao` | double | Tendência da razão adm/concluinte |
| `classificacao` | string | Classificação do desalinhamento (ex.: excesso de formação vs. escassez) |
| `ano_censo_formacao` | string | Ano do Censo usado como referência da formação |
| `versao_previsao_origem` / `versao_analise` / `dt_processamento` | string/timestamp | Rastreabilidade da previsão usada e da análise |

---

## Chaves de junção recomendadas

| Entre | Chave |
| --- | --- |
| `gold.fato_caged_semestral` ↔ `gold.dim_cbo_ocupacao` | `cbo2002_ocupacao` ↔ `codigo_cbo` (atenção ao zero à esquerda: converter com `LPAD`) |
| `gold.fato_inep_*` ↔ `gold.dim_cine_brasil` | `codigo_cine_rotulo` |
| `silver.novo_caged_movimentacoes` ↔ dicionários `ref_*` | colunas de código (ex.: `uf`, `cbo2002_ocupacao`, `tipo_movimentacao`) ↔ `codigo` |
| `gold.bridge_cine_cbo_provisoria` ↔ `gold.dim_cine_brasil` | `codigo_cine_area_especifica` ↔ `codigo_cine_area_especifica` |
| `gold.bridge_cine_cbo_provisoria` ↔ `gold.fato_caged_semestral` / `dim_cbo_ocupacao` | `codigo_cbo_subgrupo` (3 dígitos) ↔ dígitos 2 a 4 do código CBO 2002 — derivável com `LPAD(CAST(FLOOR(cbo2002_ocupacao/1000) % 1000 AS STRING), 3, '0')` |
| `gold.bridge_cine_cbo_provisoria_cobertura` ↔ `bridge_cine_cbo_provisoria` | `codigo_cine_area_especifica` + `versao_mapeamento` |
| `gold.ml_features_mensal_uf_cbo` / `previsoes_admissoes` / `desalinhamento_formacao_mercado` ↔ `bridge_cine_cbo_provisoria` | `codigo_cbo_subgrupo` (grão já no nível de 3 dígitos da bridge) |

> **Observação:** `dim_cbo_ocupacao.codigo_cbo` é STRING de 6 dígitos; `fato_caged_semestral.cbo2002_ocupacao` e `silver` usam INT (perdem o zero à esquerda). Ao cruzar, use `CAST/LPAD` para alinhar os formatos.
