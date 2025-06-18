# Tarefa: Implementar Job de Trending Topics

## Descrição
Desenvolver e implementar um job agendado para identificar e destacar os conceitos com maior crescimento de menções recentes no grafo de conhecimento do aclarai. Este job criará um arquivo Markdown (`Trending Topics - <date>.md`) contendo uma lista dinâmica de tópicos em tendência, calculada com base nos deltas de menção das arestas `SUPPORTS_CONCEPT` e `MENTIONS_CONCEPT` em um período configurável, conforme o design de páginas de destaque em `docs/arch/on-writing_vault_documents.md`.

## Escopo

### Incluído
- Implementação de um job agendado (utilizando o `aclarai-scheduler` de `docs/project/epic_1/sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`) para rastrear timestamps de criação das arestas `SUPPORTS_CONCEPT` e `MENTIONS_CONCEPT` (definidas em `docs/arch/on-linking_claims_to_concepts.md`) conectadas aos nós `(:Concept)` (definidos em `docs/arch/on-concepts.md`).
- Desenvolvimento de lógica para calcular **deltas de menção por conceito** em um período configurável (e.g., os últimos `window_days` como definido em `docs/arch/design_config_panel.md`, Seção 4: "Concept Highlight & Summary Jobs", `trending_topics.window_days`). Isso envolverá comparar a frequência de menções no período recente com um período base anterior.
- Determinação dos "top changed concepts" (conceitos mais alterados) com base nesses deltas, respeitando os parâmetros `count`, `percent`, e `min_mentions` configuráveis em `design_config_panel.md`.
- Criação ou atualização do arquivo `Trending Topics - <date>.md` no vault, com a data dinâmica no nome do arquivo (conforme `target_file` em `design_config_panel.md`).
- **Formatação do conteúdo de `Trending Topics - <date>.md`** para facilitar a navegação e a legibilidade, seguindo o padrão de "Trending Concepts Agent" em `on-writing_vault_documents.md` (Seção "Trending Concepts Agent"). Isso incluirá o nome do conceito, métricas de crescimento (percentual e/ou absoluto) e backlinks `[[wikilink]]` para as páginas de conceito correspondentes.
- **Utilização da lógica de escrita atômica para arquivos Markdown** (`.tmp` → `fsync` → `rename`) implementada em Sprint 3 (`docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md` e detalhada em `docs/arch/on-filehandle_conflicts.md`).
- Integração com o sistema de agendamento do `aclarai-scheduler` (de Sprint 3), permitindo que o job seja configurado e executado automaticamente (conforme `docs/arch/architecture.md` e `docs/project/epic_1/sprint_6-Add_configuration_controls.md`).
- Documentação clara do processo e configuração.
- Implementação de testes para verificar o correto funcionamento e a qualidade da saída.
- Garantia de que o arquivo Trending Topics - <date>.md gerado inclua seus próprios marcadores <!-- aclarai:id=file_<slug> ver=N --> (ou similar) para que o arquivo possa ser rastreado e sincronizado pelo sistema de vault (docs/arch/on-graph_vault_synchronization.md). A granularidade de aclarai:id para itens de lista individuais pode ser considerada para futuras iterações, mas o arquivo como um todo deve ser rastreável.

### Excluído
- Interface de usuário para visualização interativa (será implementada em tarefa separada em Sprint 9).
- Análise avançada de sentimento ou contexto das menções (o foco é na frequência e delta de menções).
- Otimizações avançadas de desempenho que vão além do uso eficiente de consultas Neo4j e agregação temporal.
- Previsão de tendências futuras ou modelagem preditiva.
- Geração de "blurbs" ou resumos LLM para cada conceito na página "Trending Topics" (isso é escopo do `model.trending_concepts_agent` em `design_config_panel.md`, mas não do cálculo das tendências em si para MVP).

## Critérios de Aceitação
- O job rastreia corretamente os timestamps de criação das arestas `SUPPORTS_CONCEPT` e `MENTIONS_CONCEPT` no Neo4j.
- Os deltas de menção são calculados adequadamente para o período configurado (`window_days`).
- Os "top changed concepts" são selecionados corretamente com base nos parâmetros `count`, `percent`, e `min_mentions`.
- O arquivo `Trending Topics - <date>.md` é criado ou atualizado no diretório alvo (configurável via `target_file`).
- O conteúdo do arquivo inclui os nomes dos conceitos, métricas de crescimento (e.g., número de novas menções, percentual de aumento) e backlinks `[[wikilink]]` para as páginas de conceito correspondentes, seguindo o formato de `on-writing_vault_documents.md`.
- A escrita do arquivo `Trending Topics - <date>.md` utiliza a lógica de escrita atômica de forma robusta e segura.
- A integração com o sistema de agendamento funciona corretamente, permitindo a execução automática ou manual do job.
- A documentação clara do processo e configuração está disponível.
- Testes automatizados demonstram a funcionalidade e robustez do job, incluindo o cálculo correto dos deltas e a geração do arquivo Markdown.
- O arquivo Trending Topics - <date>.md gerado inclui seus próprios marcadores aclarai:id e ver= para compatibilidade com o vault sync.

## Dependências
- Neo4j configurado e populado com nós `(:Concept)` (criados em `docs/project/epic_1/sprint_5-Create_Update_Tier_3.md`) e arestas `SUPPORTS_CONCEPT` e `MENTIONS_CONCEPT` (criadas em `docs/project/epic_1/sprint_5-Link_claims_to_concepts.md`).
- Sistema de agendamento (`aclarai-scheduler` com `APScheduler`) implementado e funcional (de `docs/project/epic_1/sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`).
- Acesso ao sistema de arquivos para criação e atualização de arquivos Markdown.
- Lógica de escrita atômica para arquivos Markdown implementada (de `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md`).
- Definição da configuração para "Trending Topics" em `docs/arch/design_config_panel.md`.

## Entregáveis
- Código-fonte do job de Trending Topics (dentro do serviço `aclarai-scheduler`).
- Implementação da lógica de cálculo de deltas de menção e seleção de conceitos em tendência.
- Geração do arquivo Markdown `Trending Topics - <date>.md` com o formato especificado.
- Documentação técnica do processo e configuração.
- Testes unitários e de integração.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Falsos positivos devido a flutuações normais de atividade ou eventos pontuais, resultando em conceitos "em tendência" que não são realmente significativos.
  - **Mitigação**: Implementar `min_mentions` (conforme `design_config_panel.md`) para filtrar ruído. Considerar normalização estatística do crescimento por volume base de menções para evitar que conceitos com poucas menções se destaquem desproporcionalmente.
- **Risco**: Desempenho inadequado com histórico muito extenso de arestas, impactando o cálculo de deltas.
  - **Mitigação**: Otimizar consultas Cypher para análise temporal (e.g., usando índices em timestamps de criação de arestas). Implementar janelas deslizantes eficientes e agregação periódica de contagens para reduzir a carga de cálculo.
- **Risco**: Resultados dominados por conceitos muito genéricos que sempre têm muitas menções, dificultando a identificação de tendências emergentes.
  - **Mitigação**: Explorar a normalização do crescimento pelo volume médio de menções do conceito ao longo do tempo. Refinar a seleção de conceitos "top changed" para priorizar aqueles com *mudança significativa* em relação à sua linha de base.

## Notas Técnicas
- Utilizar consultas Cypher eficientes para agregar contagens de arestas por conceito dentro de diferentes janelas de tempo.
- A lógica de cálculo do delta de menções deve ser configurável para `window_days` (e.g., 7 dias).
- A seleção dos conceitos em tendência deve respeitar os parâmetros `count`, `percent`, e `min_mentions`.
- O formato do arquivo `Trending Topics - <date>.md` deve seguir o exemplo de páginas de destaque em `on-writing_vault_documents.md`, utilizando `[[wikilinks]]` para os conceitos.
- O job deve ser capaz de ler e aplicar as configurações de `target_file` (nome do arquivo de saída).
- O logging detalhado da execução do job, incluindo os conceitos identificados como tendência e suas métricas, será crucial para monitoramento e calibração.
- Este job contribui diretamente para a proposta de valor de "Trending Topics / Concepts" em `docs/project/product_definition.md`.
