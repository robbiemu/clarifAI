# Tarefa: Implementar Agente de Resumo de Conceito

## Descrição
Desenvolver e implementar um agente inteligente para gerar arquivos Markdown `[[Concept]]` para cada conceito canônico no grafo de conhecimento. Este agente extrairá informações relevantes de claims, resumos, enunciados e conceitos relacionados (conforme definido em `docs/arch/on-RAG_workflow.md` para o fluxo RAG de conceitos) para criar páginas de conceito informativas e bem estruturadas, seguindo o formato especificado em `docs/arch/on-writing_vault_documents.md` (Seção "Concept Summary Agent").

## Escopo

### Incluído
- Implementação de um agente para gerar arquivos Markdown `[[Concept]]` para cada conceito canônico (definido em `docs/arch/on-concepts.md`).
- Desenvolvimento de lógica para extrair claims de suporte, resumos, enunciados e conceitos relacionados, utilizando as fontes de recuperação detalhadas em `on-RAG_workflow.md`.
- Criação de estrutura padronizada para páginas de conceito, incluindo:
    - Cabeçalho `## Concept: <concept name>`
    - Exemplos em bullet-point com `^clarifai:id` (conforme `docs/arch/idea-creating_tier1_documents.md`)
    - Seção "See Also" com conceitos relacionados
    (Esta estrutura segue `on-writing_vault_documents.md`).
- Implementação de critérios para pular conceitos com links de claim insuficientes, conforme a configuração `skip_if_no_claims` em `docs/arch/design_config_panel.md` (Seção 4: "Concept Summary Agent").
- **Utilização da lógica de escrita atômica para arquivos Markdown** (`.tmp` → `fsync` → `rename`) implementada em Sprint 3 (`docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md` e detalhada em `docs/arch/on-filehandle_conflicts.md`).
- Integração com o grafo de conhecimento (Neo4j) e sistema de arquivos para leitura de dados e escrita de arquivos.
- Documentação clara do processo e formato de saída.
- Implementação de testes para verificar a correta geração das páginas de conceito.

### Excluído
- Interface de usuário para edição de conceitos.
- Geração de conteúdo a partir de fontes externas (conforme `on-writing_vault_documents.md`, Notas: "No external search is used.").
- Otimizações avançadas de desempenho.
- Processamento em lote de grandes volumes de dados que excedam a capacidade de uma execução periódica.
- Análise avançada de relações entre conceitos (além da recuperação para "See Also").

## Critérios de Aceitação
- Agente gera arquivos Markdown `[[Concept]]` com estrutura padronizada (conforme `on-writing_vault_documents.md`).
- Conteúdo inclui informações relevantes de claims, resumos, enunciados e conceitos relacionados (conforme `on-RAG_workflow.md`).
- A estrutura do arquivo segue o formato especificado (cabeçalho, exemplos, "See Also").
- Conceitos com links de claim insuficientes são adequadamente ignorados (respeitando a configuração `skip_if_no_claims`).
- A integração funciona corretamente com o grafo de conhecimento e sistema de arquivos.
- A escrita do arquivo `[[Concept]]` utiliza a lógica de escrita atômica de forma robusta e segura.
- Documentação clara do processo e formato está disponível.
- Testes demonstram funcionalidade e robustez do agente.

## Dependências
- Grafo de conhecimento com nós `(:Concept)` (criados em `docs/project/epic_1/sprint_5-Create_Update_Tier_3.md`), `(:Claim)` (de `docs/project/epic_1/sprint_3-Create_nodes_in_neo4j.md`), `(:Summary)` (de `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md`) e seus relacionamentos (e.g., `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT` de `docs/project/epic_1/sprint_5-Link_claims_to_concepts.md`).
- Sistema de embeddings para identificação de conceitos relacionados e recuperação de enunciados (o `utterances` vector store de `docs/project/epic_1/sprint_2-Embed_utterance_chunks.md` e o `concepts` vector store de `docs/project/epic_1/sprint_5-hnswlib.md`).
- Acesso ao sistema de arquivos para criação de arquivos Markdown.
- Definição clara do formato de páginas de conceito (em `on-writing_vault_documents.md` e `design_config_panel.md`).
- Lógica de escrita atômica para arquivos Markdown implementada (de `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md`).

## Entregáveis
- Código-fonte do agente de resumo de conceito (dentro do serviço `clarifai-core` ou `scheduler`).
- Implementação de extração de informações relevantes do grafo e vector stores.
- Geração de arquivos Markdown com estrutura padronizada.
- Documentação técnica do processo e formato.
- Testes unitários e de integração.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Qualidade inconsistente dos resumos gerados (e.g., resumos superficiais, imprecisos).
  - **Mitigação**: Iteração e ajuste dos prompts do agente de resumo; implementação de métricas de qualidade básicas para resumos (e.g., coerência, concisão) e feedback para ajuste de prompts.
- **Risco**: Conceitos com informações insuficientes resultando em páginas vazias ou de baixa qualidade.
  - **Mitigação**: Implementar a configuração `skip_if_no_claims` (de `design_config_panel.md`) para evitar a geração de páginas para conceitos sem suporte. Estabelecer thresholds mínimos para a quantidade de informações recuperadas antes da geração.
- **Risco**: Desempenho inadequado com grande número de conceitos a serem processados.
  - **Mitigação**: Implementar processamento incremental (apenas para conceitos novos ou alterados); otimizar as consultas ao grafo e vector stores para recuperação de dados.

## Notas Técnicas
- Utilizar prompts cuidadosamente projetados para o LLM, instruindo-o sobre a estrutura e o conteúdo esperado para a página de conceito, conforme `on-writing_vault_documents.md`.
- Considerar o uso de templates para garantir estrutura uniforme das páginas de conceito.
- O agente deve ser capaz de receber o modelo LLM a ser utilizado via configuração (e.g., `model.concept_summary` de `design_config_panel.md`).
- A recuperação de exemplos (`max_examples`) e a inclusão da seção "See Also" (`include_see_also`) devem ser configuráveis via `design_config_panel.md`.
- O logging detalhado da geração de cada página de conceito, incluindo o `concept_id` e as fontes de dados utilizadas, será crucial para depuração e rastreabilidade.
- Este job contribui para a proposta de valor de "Dedicated Concept Pages" em `docs/project/product_definition.md`.
