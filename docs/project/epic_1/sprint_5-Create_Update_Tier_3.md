# Tarefa: Criar/atualizar arquivos Markdown Tier 3 ([[Concept]]) e nós (:Concept)

## Descrição
Desenvolver um sistema para criar e atualizar arquivos Markdown Tier 3 (`[[Concept]]`) no vault e seus correspondentes nós `(:Concept)` no grafo de conhecimento Neo4j. Este sistema será acionado por **candidatos a conceito "promovidos"** pela lógica de detecção baseada em embeddings (`hnswlib` de Sprint 4), estabelecendo a camada conceitual canônica do ClarifAI.

## Escopo

### Incluído
- Implementação de um sistema para processar **candidatos a conceito marcados como "promoted"** na tabela `concept_candidates` (output da tarefa de Sprint 4 "Usar hnswlib para detecção de conceitos baseada em embeddings").
- Desenvolvimento de lógica para:
    - **Criar novos arquivos Markdown Tier 3** para cada conceito "promovido" no diretório configurado em `paths.concepts` (conforme `on-vault_layout_and_type_inference.md`). O formato desses arquivos deve seguir o padrão de `on-writing_vault_documents.md` (seção "Concept Summary Agent").
    - **Criar um novo nó `(:Concept)` correspondente no Neo4j** para cada conceito "promovido".
    - **Atualizar nós `(:Concept)` existentes** se um candidato "promovido" for semanticamente similar a um conceito já existente (e.g., adicionando novos `aliases` ou atualizando `last_seen`).
- Para cada nó `(:Concept)` criado/atualizado, persistir as propriedades essenciais no Neo4j: `name`, `embedding_hash` (hash do texto que gerou o embedding), `last_updated`, `version` (inicialmente `1`), e `status` (e.g., `"active"`) conforme `on-concepts.md`.
- Garantir que a **escrita de arquivos Markdown Tier 3 utilize a lógica de escrita atômica** (`.tmp` → `fsync` → `rename`) já implementada (de Sprint 3, detalhada em `on-filehandle_conflicts.md`).
- Documentação detalhada do sistema de criação e atualização de conceitos, incluindo o fluxo de dados dos candidatos a conceito.
- Implementação de testes para verificar a correta criação de arquivos Markdown e nós `(:Concept)`, a atualização de propriedades e a prevenção de duplicação.

### Excluído
- A lógica de extração de frases nominais (`on-noun_phrase_extraction.md`, tarefa de Sprint 4).
- A lógica de detecção de similaridade e marcação de candidatos como "promoted" ou "merged" (`hnswlib`, tarefa de Sprint 4). Esta tarefa **consome** o resultado.
- Geração de conteúdo definicional para os conceitos via LLM (será implementada em tarefa posterior, Sprint 9 "Implement Concept Summary Agent").
- Vinculação de claims a conceitos (tarefa "Link claims to concepts with SUPPORTS\_CONCEPT, MENTIONS\_CONCEPT, etc." deste sprint).
- Refresco periódico de embeddings de conceitos baseados em edições manuais (tarefa "Refresh embeddings from concept files nightly" de Sprint 5).
- Sincronização automática em tempo real entre o vault e o grafo para edições manuais de arquivos Tier 3 (coberto por `vault-watcher` de Sprint 4 e `Block Syncing Loop` de Sprint 4). Esta tarefa foca na **criação inicial/promoção**.
- Interface de usuário para edição de conceitos ou visualização do grafo.

## Critérios de Aceitação
- O sistema processa corretamente os candidatos a conceito marcados como "promoted" na tabela `concept_candidates`.
- Para cada conceito "promovido", um novo arquivo Markdown Tier 3 é criado no diretório `paths.concepts`, com um nome canônico e o formato padrão.
- Um novo nó `(:Concept)` é criado no Neo4j para cada novo conceito, com as propriedades `name`, `embedding_hash`, `last_updated`, `version=1`, e `status="active"` populadas corretamente.
- Se um conceito "promovido" já existe (identificado por similaridade), o nó `(:Concept)` existente é atualizado (e.g., `last_updated`, `aliases` se aplicável).
- A escrita de arquivos Markdown Tier 3 utiliza a lógica de escrita atômica de forma robusta e segura.
- Documentação clara e precisa do fluxo de dados para a criação e atualização de conceitos.
- Testes automatizados demonstram a funcionalidade e robustez da criação e atualização de conceitos, incluindo cenários de novos conceitos e atualização de conceitos existentes.

## Dependências
- Sistema de extração de frases nominais (`sprint_4-Create_noun_phrase_extractor.md`) para gerar candidatos.
- Sistema de detecção de conceitos baseado em embeddings (`sprint_4-hnswlib.md`) que classifica candidatos como "promoted".
- Neo4j configurado e acessível para armazenar nós `(:Concept)`.
- Acesso ao sistema de arquivos para criação de arquivos Markdown.
- Definição clara do formato de arquivos Concept e suas propriedades (`on-writing_vault_documents.md`, `on-concepts.md`).
- A lógica de escrita atômica para arquivos Markdown implementada (de Sprint 3, referenciada em `on-filehandle_conflicts.md`).

## Entregáveis
- Código-fonte do sistema de criação e atualização de conceitos (dentro de `clarifai-core`).
- Implementação da lógica de interação com o Neo4j para nós `(:Concept)`.
- Documentação do sistema e seu funcionamento.
- Testes unitários e de integração.
- Exemplos de arquivos Concept gerados e de nós `(:Concept)` criados/atualizados no Neo4j.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Inconsistências entre arquivos Markdown e o grafo `(:Concept)` (e.g., um nó existir sem o arquivo ou vice-versa).
  - **Mitigação**: Implementar verificações de integridade durante o processo de criação/atualização para garantir que tanto o nó quanto o arquivo sejam criados/atualizados; a sincronização periódica do vault (`sync_vault_to_graph` de Sprint 3) servirá como fallback para correção de inconsistências.
- **Risco**: Duplicação indesejada de conceitos devido a falhas na detecção ou promoção.
  - **Mitigação**: O uso rigoroso da lógica de detecção de `hnswlib` (tarefa de Sprint 4) é a principal mitigação. Implementar testes de regressão com cenários de "quase-duplicatas".
- **Risco**: Problemas de desempenho ao criar/atualizar um grande número de conceitos simultaneamente.
  - **Mitigação**: Implementar processamento em lote (`batch processing`) para interações com o Neo4j e a escrita de arquivos; otimizar as consultas Cypher para criação/atualização de nós.

## Notas Técnicas
- O sistema deve operar sobre os `concept_candidates` que foram marcados como `"promoted"`.
- O nome do arquivo Markdown Tier 3 deve ser canônico e derivado do `name` do conceito para facilitar a vinculação e evitar problemas de sistema de arquivos.
- A criação de nós `(:Concept)` deve incluir todas as propriedades definidas em `on-concepts.md` (`name`, `embedding_hash`, `last_updated`, `version`, `status`). O `embedding_hash` deve ser calculado a partir do texto que *será escrito no arquivo Markdown* (mesmo que inicialmente esse texto seja apenas um nome/slug).
- Utilizar transações no Neo4j para garantir a atomicidade das operações de criação/atualização de nós.
- A lógica de persistência para o nó `(:Concept)` deve ser robusta, lidando com erros de conexão ou escrita.
- O sistema deve garantir que o `clarifai:id` e o `^anchor` sejam inseridos corretamente nos novos arquivos Tier 3, alinhados com o `concept_id` gerado.
