# Tarefa: Vincular claims a conceitos com SUPPORTS_CONCEPT, MENTIONS_CONCEPT, etc.

## Descrição
Implementar um sistema para vincular `(:Claim)` nodes a `(:Concept)` nodes no grafo de conhecimento, utilizando um agente LLM para classificar a natureza da relação (e.g., `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`, `CONTRADICTS_CONCEPT`). Esta tarefa estabelecerá as conexões semânticas fundamentais entre o conteúdo extraído e os conceitos identificados.

**Nota sobre Qualidade dos Claims:** Os `(:Claim)` nodes são criados em Sprint 3 com propriedades para `entailed_score`, `coverage_score`, e `decontextualization_score`, mas seus *valores* são `null` ou placeholders nesta fase (serão calculados e populados em Sprint 7 pelos agentes de avaliação). Portanto, a decisão de criar `SUPPORTS_CONCEPT` vs. `MENTIONS_CONCEPT` será baseada **exclusivamente na classificação do LLM**, e a aplicação de filtros de qualidade baseados nos scores do `(:Claim)` node (conforme `technical_overview.md`, Seção IV.C) ocorrerá em uma tarefa subsequente (após Sprint 7).

## Escopo

### Incluído
- Implementação de um sistema para:
    - **Buscar `(:Claim)` nodes** do grafo Neo4j que precisam ser vinculados (priorizando os recém-criados ou não vinculados).
    - **Identificar `(:Concept)` nodes candidatos** para vinculação, utilizando busca de similaridade no `concepts` vector store (populado por tarefa anterior de Sprint 5).
- Desenvolvimento de um **Agente LLM para classificação de relacionamento** (conforme `on-linking_claims_to_concepts.md`):
    - Analisar claims e seus conceitos candidatos.
    - Classificar a relação como `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`, ou `CONTRADICTS_CONCEPT`.
    - Calcular a `strength` (força) do relacionamento (float entre 0.0 e 1.0) baseada na confiança do LLM.
- **Criação de relacionamentos no Neo4j**:
    - Criar edges entre `(:Claim)` e `(:Concept)` nodes com o tipo de relacionamento classificado pelo LLM.
    - Armazenar a propriedade `strength` na edge.
    - **Preencher `entailed_score` e `coverage_score` nas edges copiando os valores (incluindo `null`) dos `(:Claim)` nodes de origem.**
- **Atualização de arquivos Markdown Tier 2**:
    - Inserir `[[wikilinks]]` para os conceitos relevantes diretamente no Markdown dos arquivos Tier 2 (`on-writing_vault_documents.md`, seção "Tier 2 Summary Agent").
    - Utilizar a lógica de **escrita atômica para arquivos Markdown** (já implementada em Sprint 3, detalhada em `on-filehandle_conflicts.md`).
- Documentação detalhada do sistema de vinculação e seu funcionamento.
- Implementação de testes para verificar a correta vinculação e a robustez do processo.
- Garantia de que, ao atualizar arquivos Markdown Tier 2, os marcadores aclarai:id e ver= existentes nos blocos modificados sejam preservados e que a propriedade ver= seja incrementada, para compatibilidade com o sistema de sincronização do vault (docs/arch/on-graph_vault_synchronization.md).

### Excluído
- Interface de usuário para visualização ou gerenciamento de vinculações.
- Vinculação avançada entre conceitos (ex: `RELATED_TO` entre `(:Concept)` nodes, será implementada em tarefa separada).
- Otimizações avançadas de desempenho que vão além de consultas eficientes e processamento em lote.
- **Cálculo ou geração dos scores de qualidade dos claims (`entailed_score`, `coverage_score`, `decontextualization_score`)**. Estes são responsabilidade dos agentes de avaliação em Sprint 7.
- **Aplicação de filtros de qualidade baseados nesses scores para determinar se uma edge `SUPPORTS_CONCEPT` ou `CONTRADICTS_CONCEPT` pode ser criada**. Esta lógica será adicionada em uma sprint posterior (após Sprint 7).
- Re-processamento de claims para atualizar ou refinar edges após a conclusão dos agentes de avaliação.

## Critérios de Aceitação
- O sistema busca corretamente `(:Claim)` nodes e identifica `(:Concept)` candidates relevantes usando busca de similaridade.
- O Agente LLM classifica com precisão a relação entre claims e conceitos como `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`, ou `CONTRADICTS_CONCEPT`.
- A `strength` do relacionamento é calculada e armazenada corretamente na edge.
- Relacionamentos são criados no Neo4j com o tipo correto e a propriedade `strength`.
- As propriedades `entailed_score` e `coverage_score` nas edges **refletem os valores (incluindo `null`) dos `(:Claim)` nodes de origem** nesta sprint.
- O sistema lida graciosamente com valores `null` para `entailed_score` e `coverage_score` ao copiá-los para as edges.
- Arquivos Markdown Tier 2 são atualizados com `[[wikilinks]]` para os conceitos, utilizando a escrita atômica.
- Documentação clara e precisa do sistema de vinculação e seu funcionamento, incluindo as limitações temporárias dos scores de qualidade.
- Testes automatizados demonstram a funcionalidade e robustez, cobrindo cenários de diferentes tipos de relacionamento e a correta atualização do grafo e dos arquivos Markdown.
- Arquivos Markdown Tier 2 são atualizados com [[wikilinks]] para os conceitos, e os marcadores aclarai:id e ver= dos blocos modificados são preservados e o ver= incrementado.

## Dependências
- `(:Claim)` nodes extraídos e armazenados no grafo (de Sprint 3), com propriedades de score (mesmo que `null`).
- `(:Concept)` nodes e seus arquivos Markdown Tier 3 criados e atualizados (da tarefa "Criar/atualizar arquivos Markdown Tier 3 ([[Concept]]) e nós (:Concept)" desta Sprint 5).
- O `concepts` vector store populado (da tarefa "Criar/atualizar arquivos Markdown Tier 3..." desta Sprint 5).
- Acesso a um modelo LLM configurado para classificação.
- Acesso ao Neo4j para criação de relacionamentos.
- Acesso ao sistema de arquivos para atualização de arquivos Markdown (e a lógica de escrita atômica já implementada em Sprint 3).

## Entregáveis
- Código-fonte do sistema de vinculação de claims a conceitos (incluindo o Agente LLM).
- Implementação da lógica de criação de edges no Neo4j com propriedades.
- Documentação do sistema e seu funcionamento.
- Testes unitários e de integração.
- Exemplos de vinculações criadas no grafo e de arquivos Markdown Tier 2 atualizados.

## Estimativa de Esforço
- 8 dias de trabalho

## Riscos e Mitigações
- **Risco**: Qualidade da classificação do LLM (vinculações incorretas ou irrelevantes).
  - **Mitigação**: Iteração e ajuste dos prompts do Agente LLM; implementação de testes de regressão com conjuntos de dados rotulados; definição de um `threshold` para a `strength` do LLM antes de criar a edge.
- **Risco**: Desempenho inadequado com grande volume de claims a serem vinculados.
  - **Mitigação**: Implementar processamento em lotes (`batch processing`) para chamadas ao LLM e para atualizações no Neo4j; otimizar consultas ao grafo e ao vector store.
- **Risco**: Inconsistências entre o grafo e os arquivos Markdown devido a erros na atualização.
  - **Mitigação**: A utilização estrita da escrita atômica (`.tmp` -> `fsync` -> `rename`) é a principal mitigação para a segurança dos arquivos. Implementar verificações de integridade pós-escrita e logging detalhado.
- **Risco**: O faseamento dos scores de qualidade pode causar confusão ou necessidade de re-trabalho significativo em sprints futuras.
  - **Mitigação**: Documentar claramente as limitações da implementação atual e o plano para a fase de refinamento pós-Sprint 7. Assegurar que os testes cubram a transição futura dos scores de qualidade.
- **Risco**: Erro ou comportamento inesperado ao lidar com valores `null` ao copiar scores para as edges.
  - **Mitigação**: Implementar tratamento explícito para `null`s (e.g., copiá-los diretamente, ou definir um valor padrão se a propriedade não permitir `null`); incluir casos de teste específicos para cenários com `null` scores.

## Notas Técnicas
- O Agente LLM deve ser configurável, permitindo a seleção de diferentes modelos (conforme `design_config_panel.md`).
- A recuperação de conceitos candidatos deve utilizar a busca de similaridade no `concepts` vector store, que será populado por outra tarefa desta sprint.
- A lógica de patching de Markdown deve ser robusta para inserir wikilinks sem corromper o conteúdo existente ou os `aclarai:id` anchors.
- Assegurar que as transações do Neo4j sejam utilizadas para garantir a atomicidade das operações de criação de edges.
- O logging detalhado de cada classificação e criação de edge será crucial para depuração e monitoramento da qualidade.
