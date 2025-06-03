# Tarefa: Implementar Job de Top Concepts

## Descrição
Desenvolver e implementar um job agendado para identificar e destacar os conceitos mais importantes do grafo de conhecimento, utilizando algoritmos de centralidade como PageRank nos nós `(:Concept)` do Neo4j. O resultado será um arquivo Markdown (`Top Concepts.md`) listando os conceitos mais relevantes do sistema, sua classificação e backlinks, conforme o design de páginas de destaque em `docs/arch/on-writing_vault_documents.md`.

## Escopo

### Incluído
- Implementação de um job agendado (utilizando o `clarifai-scheduler` de Sprint 3) para executar PageRank nos nós `(:Concept)` do Neo4j.
- Desenvolvimento de lógica para selecionar os top N conceitos por pontuação de PageRank, onde N é configurável via `docs/arch/design_config_panel.md` (Seção 4: "Concept Highlight & Summary Jobs", `top_concepts.count` ou `percent`).
- Criação ou atualização do arquivo `Top Concepts.md` no vault, listando os conceitos selecionados, sua classificação (rank) e backlinks.
- **Formatação do conteúdo de `Top Concepts.md`** para facilitar a navegação e a legibilidade, seguindo o padrão de "Trending Concepts Agent" em `docs/arch/on-writing_vault_documents.md` (Seção "Trending Concepts Agent").
- **Utilização da lógica de escrita atômica para arquivos Markdown** (`.tmp` → `fsync` → `rename`) implementada em Sprint 3 (`docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md` e detalhada em `docs/arch/on-filehandle_conflicts.md`).
- Integração com o sistema de agendamento do `clarifai-scheduler` (de Sprint 3), permitindo que o job seja configurado e executado automaticamente (conforme `docs/arch/architecture.md` e `docs/project/epic_1/sprint_6-Add_configuration_controls.md`).
- Documentação clara do processo e configuração.
- Implementação de testes para verificar o correto funcionamento e a qualidade da saída.
- Garantia de que o arquivo Top Concepts.md gerado inclua seus próprios marcadores <!-- clarifai:id=file_<slug> ver=N --> (ou similar) para que o arquivo possa ser rastreado e sincronizado pelo sistema de vault (docs/arch/on-graph_vault_synchronization.md). A granularidade de clarifai:id para itens de lista individuais pode ser considerada para futuras iterações, mas o arquivo como um todo deve ser rastreável.

## Critérios de Aceitação
- O job executa PageRank corretamente nos nós `(:Concept)` do Neo4j (definidos em `docs/arch/on-concepts.md`).
- Os top N conceitos são selecionados adequadamente por pontuação de PageRank, respeitando o número configurável (N).
- O arquivo `Top Concepts.md` é criado ou atualizado no diretório alvo (configurável via `target_file`).
- O conteúdo de `Top Concepts.md` inclui os nomes dos conceitos, sua classificação (rank) e backlinks `[[wikilink]]` para as páginas de conceito correspondentes, seguindo o formato de `on-writing_vault_documents.md`.
- A escrita do arquivo `Top Concepts.md` utiliza a lógica de escrita atômica de forma robusta e segura.
- A integração com o sistema de agendamento funciona corretamente, permitindo a execução automática ou manual do job.
- A documentação clara do processo e configuração está disponível.
- Testes automatizados demonstram a funcionalidade e robustez do job, incluindo a seleção correta dos conceitos e a geração do arquivo Markdown.
- O arquivo Top Concepts.md gerado inclui seus próprios marcadores clarifai:id e ver= para compatibilidade com o vault sync.

## Dependências
- Neo4j configurado e populado com nós `(:Concept)` (criados em `docs/project/epic_1/sprint_5-Create_Update_Tier_3.md`).
- Sistema de agendamento (`clarifai-scheduler` com `APScheduler`) implementado e funcional (de `docs/project/epic_1/sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`).
- Acesso ao sistema de arquivos para criação e atualização de arquivos Markdown.
- Lógica de escrita atômica para arquivos Markdown implementada (de `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md`).
- Definição da configuração para "Top Concepts" em `docs/arch/design_config_panel.md`.

## Entregáveis
- Código-fonte do job de Top Concepts (dentro do serviço `clarifai-scheduler`).
- Implementação da lógica de execução de PageRank e seleção de conceitos.
- Geração do arquivo Markdown `Top Concepts.md` com o formato especificado.
- Documentação técnica do processo e configuração.
- Testes unitários e de integração.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Desempenho inadequado com grande número de conceitos no grafo, impactando o cálculo de PageRank.
  - **Mitigação**: Otimizar consultas Cypher para cálculo de PageRank e seleção dos top N. Considerar a frequência de execução do job (e.g., semanal em vez de diária para grafos muito grandes).
- **Risco**: Os conceitos selecionados não refletem a importância real ou são muito genéricos/irrelevantes.
  - **Mitigação**: Calibrar o algoritmo de PageRank (e.g., ponderando arestas se aplicável). A configuração de `metric` permite flexibilidade futura para tentar outras métricas de centralidade como `degree`.
- **Risco**: Arquivo `Top Concepts.md` gerado muito grande ou difícil de navegar em vaults com muitos conceitos.
  - **Mitigação**: Implementar a configuração de `count` ou `percent` para limitar o número de conceitos exibidos. A formatação em lista com backlinks deve ser concisa.

## Notas Técnicas
- Utilizar os algoritmos de centralidade de grafo nativos do Neo4j (Graph Data Science Library) para o cálculo eficiente de PageRank.
- A seleção dos top N conceitos deve ser baseada no valor configurado em `clarifai.config.yaml` (`top_concepts.count` ou `top_concepts.percent`).
- O formato do arquivo `Top Concepts.md` deve seguir o exemplo de páginas de destaque em `on-writing_vault_documents.md`, utilizando `[[wikilinks]]` para os conceitos.
- O job deve ser capaz de ler e aplicar as configurações de `target_file` (nome do arquivo de saída) e `metric` (PageRank ou Degree).
- O logging detalhado da execução do job, incluindo o número de conceitos processados e os top N selecionados, será crucial para monitoramento.
- Este job contribui diretamente para a proposta de valor de "Top Concept Page" em `docs/project/product_definition.md`.
