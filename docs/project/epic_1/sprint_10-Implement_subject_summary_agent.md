# Tarefa: Implementar Subject Summary Agent

## Descrição
Desenvolver e implementar um agente inteligente para gerar arquivos Markdown `[[Subject:XYZ]]` para cada cluster de conceitos relacionados. Este agente extrairá informações relevantes de claims compartilhados, resumos comuns e conceitos principais, com a capacidade de utilizar pesquisa web para fornecer contexto adicional. A geração seguirá o formato e as configurações detalhadas em `docs/arch/on-writing_vault_documents.md` e `docs/arch/design_config_panel.md`.

## Escopo

### Incluído
- Implementação do **Subject Summary Agent**, conforme descrito em `docs/arch/on-writing_vault_documents.md` (Seção "Subject Summary Agent").
- Desenvolvimento de lógica para extrair informações relevantes do grafo: claims compartilhados, resumos comuns, e nomes dos principais `(:Concept)` nodes dentro de cada cluster.
- Implementação da capacidade de pesquisa web ou uso de referências de código aberto para contexto adicional, controlada pela configuração `allow_web_search` (conforme `docs/arch/design_config_panel.md`).
- Criação de estrutura padronizada para páginas de assunto, incluindo:
  - Cabeçalho `## Subject: <name or synthesized theme>`
  - Lista de `[[Concept]]`s membros com backlinks
  - Resumo em seções de temas ou questões-chave
  - Inclusão dos marcadores `<!-- aclarai:id=subject_<slug> ver=N -->` e `^subject_<slug>` para compatibilidade com o sistema de sincronização do vault (`docs/arch/on-graph_vault_synchronization.md`).
  (Esta estrutura segue `docs/arch/on-writing_vault_documents.md`).
- O comportamento do agente será configurável via `settings/aclarai.config.yaml` (gerenciado pela UI de Sprint 10), incluindo:
  - `model.subject_summary` (modelo LLM a ser utilizado, conforme `docs/arch/design_config_panel.md`).
  - `similarity_threshold` para formação de clusters (embora a formação do cluster seja em outra tarefa, o agente pode usar para coerência, conforme `docs/arch/design_config_panel.md`).
  - `min_concepts` e `max_concepts` para o tamanho do cluster.
  - `allow_web_search` (toggle).
  - `skip_if_incoherent` (toggle para evitar geração de assuntos sem coesão).
- **Utilização da lógica de escrita atômica para arquivos Markdown** (`.tmp` → `fsync` → `rename`) implementada em `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md` e detalhada em `docs/arch/on-filehandle_conflicts.md`.
- Integração com o sistema de clustering de conceitos (que fornecerá os clusters de entrada).
- Documentação clara do processo, formato de saída e opções de configuração.
- Implementação de testes para verificar a correta geração das páginas de assunto em diversos cenários.

### Excluído
- Interface de usuário para edição de assuntos (o foco é na geração automática).
- Vinculação avançada entre assuntos (será implementada em tarefa separada, "Link Concepts to Subjects" de Sprint 10).
- Otimizações avançadas de desempenho que vão além de um uso eficiente de LLMs e cache de pesquisa web.
- Processamento em lote de volumes *extremamente* grandes de dados (foco na funcionalidade e correção).
- Análise avançada de relações entre assuntos (além da recuperação para o resumo).

## Critérios de Aceitação
- O agente gera arquivos Markdown `[[Subject:XYZ]]` com a estrutura padronizada especificada em `docs/arch/on-writing_vault_documents.md`.
- O conteúdo das páginas de assunto inclui informações relevantes de claims compartilhados, resumos comuns e nomes dos principais conceitos, puxados do grafo.
- A capacidade de pesquisa web funciona corretamente quando `allow_web_search` está habilitada, e as referências são incorporadas de forma relevante.
- A estrutura do arquivo segue o formato especificado (cabeçalho, conceitos membros, resumo em seções) e inclui os marcadores `aclarai:id` e `ver=`.
- O agente respeita e aplica as configurações lidas do `aclarai.config.yaml` (`model.subject_summary`, `similarity_threshold`, `min_concepts`, `max_concepts`, `allow_web_search`, `skip_if_incoherent`).
- A escrita do arquivo `[[Subject:XYZ]]` utiliza a lógica de escrita atômica de forma robusta e segura.
- A integração com o sistema de clustering de conceitos funciona corretamente, recebendo os clusters de entrada.
- A documentação clara do processo, formato e opções de configuração está disponível.
- Testes automatizados demonstram a funcionalidade e robustez do agente, incluindo cenários de geração bem-sucedida, clusters incoerentes (se `skip_if_incoherent` ativado), e uso/não-uso da pesquisa web.

## Dependências
- Sistema de clustering de conceitos implementado (`docs/project/epic_1/sprint_10-Implement_Concept_clustering_job.md`), fornecendo os clusters de conceitos como entrada.
- Acesso ao Neo4j para consulta de `(:Concept)`, `(:Claim)` e `(:Summary)` nodes e seus relacionamentos (`docs/project/epic_1/sprint_3-Create_nodes_in_neo4j.md`, `docs/project/epic_1/sprint_5-Link_claims_to_concepts.md`).
- Acesso à internet para pesquisa web (quando habilitado e configurado).
- Acesso ao sistema de arquivos para criação de arquivos Markdown.
- Definição clara do formato de páginas de assunto em `docs/arch/on-writing_vault_documents.md` e `docs/arch/design_config_panel.md`.
- Lógica de escrita atômica para arquivos Markdown implementada (`docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md`).
- Configuração de `model.subject_summary` disponível via `aclarai.config.yaml` (gerenciada pela UI de Sprint 10).

## Entregáveis
- Código-fonte do Subject Summary Agent (dentro do serviço `aclarai-core` ou `scheduler`).
- Implementação da lógica de extração de informações relevantes do grafo.
- Implementação da capacidade de pesquisa web para contexto adicional (se `allow_web_search` for `true`).
- Geração de arquivos Markdown `[[Subject:XYZ]]` com estrutura padronizada e metadados `aclarai:id`/`ver=`.
- Documentação técnica do processo e formato.
- Testes unitários e de integração.

## Estimativa de Esforço
- 4 dias de trabalho

## Riscos e Mitigações
- **Risco**: Qualidade inconsistente dos resumos gerados (e.g., resumos superficiais, imprecisos, ou que não refletem bem o cluster).
  - **Mitigação**: Iteração e ajuste dos prompts do LLM para o agente de resumo; implementação de métricas de qualidade básicas para resumos (e.g., coerência, concisão) e feedback para ajuste de prompts. Realizar testes de regressão com exemplos "golden standard".
- **Risco**: Informações incorretas ou alucinadas de fontes web (se `allow_web_search` habilitado).
  - **Mitigação**: Implementar verificação cruzada (se possível, com outras fontes ou com o próprio grafo) e priorizar fontes confiáveis. Limitar a profundidade da pesquisa e o volume de texto externo introduzido.
- **Risco**: Assuntos com informações insuficientes ou clusters incoerentes resultando em páginas vazias ou de baixa qualidade.
  - **Mitigação**: Utilizar a configuração `skip_if_incoherent` para evitar a geração de páginas para clusters que o agente considera sem coesão. Estabelecer `min_concepts` para garantir um tamanho mínimo de cluster.
- **Risco**: Consumo excessivo de tokens LLM ou requisições de pesquisa web.
  - **Mitigação**: Otimizar o design dos prompts para serem concisos. Implementar um sistema de cache para resultados de pesquisa web para evitar requisições repetidas para a mesma consulta.

## Notas Técnicas
- O agente deve ser capaz de receber o modelo LLM a ser utilizado via configuração (`model.subject_summary`).
- A lógica de recuperação de informações deve ser robusta, lidando com clusters de diferentes tamanhos e densidades.
- A pesquisa web deve ser um componente modular e configurável, com tratamento de erros para falhas de rede ou APIs.
- O formato do arquivo de saída deve ser rigorosamente consistente com `on-writing_vault_documents.md` para garantir a compatibilidade com Obsidian e o sistema de sincronização.
- O logging detalhado da geração de cada página de assunto, incluindo o `subject_id` e as fontes de dados utilizadas (grafo e/ou web), será crucial para depuração e rastreabilidade.
- Este job contribui diretamente para a proposta de valor de "Subject Pages" em `docs/project/product_definition.md`.
