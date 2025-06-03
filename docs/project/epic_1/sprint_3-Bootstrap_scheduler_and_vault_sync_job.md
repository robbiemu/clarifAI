# Tarefa: Inicializar contêiner do agendador + job de sincronização do vault

## Descrição
Desenvolver e configurar um contêiner de agendador (scheduler) para o ClarifAI, implementando um job de sincronização do vault que mantenha a consistência entre os arquivos Markdown e o grafo de conhecimento no Neo4j, detectando blocos alterados por hash e atualizando o grafo.

## Escopo

### Incluído
- Adição de um novo serviço `clarifai-scheduler` ao monorepo (diretório `services/scheduler/`).
- Configuração do `APScheduler` para executar jobs em uma programação cron (e.g., diariamente às 2h), conforme a estratégia de `architecture.md`.
- Implementação do job `sync_vault_to_graph()`:
    - **Leitura e parsing** de todos os arquivos Markdown Tier 1 (e, opcionalmente, Tier 2 e Tier 3, se o escopo permitir a generalização da detecção de `clarifai:id` em todos os tiers).
    - **Cálculo de hash do conteúdo visível** (`semantic_text` conforme `on-refreshing_concept_embeddings.md`, stripping metadata) para cada bloco com `clarifai:id` e `^anchor`.
    - Comparação do hash calculado com o hash (`embedding_hash` ou similar) armazenado no Neo4j para o nó correspondente (`:Block`, `:Claim`, `:Concept`).
    - Atualização das propriedades dos nós no Neo4j (e.g., `text`, `hash`, `last_updated`) e marcação como "dirty" (`needs_reprocessing: true`) quando o conteúdo do bloco Markdown for alterado (conforme `on-graph_vault_synchronization.md`, "Block Diffing").
    - **Incremento da propriedade `ver=` (versão)** para blocos alterados no grafo, conforme `on-graph_vault_synchronization.md`.
- Implementação de logging detalhado para o início, término, e resultado da execução do job, incluindo o número de blocos processados e alterados.
- Configuração do contêiner Docker para o serviço de agendador (`services/scheduler/Dockerfile`).
- Documentação do serviço e do job de sincronização.

### Excluído
- Interface de usuário para controle do agendador (será implementada em Sprint 6).
- Sistema de filas externas para jobs (APScheduler gerenciará internamente).
- Controles avançados de automação (e.g., pausas globais ou por job) que serão implementados em Sprint 6.
- Otimizações avançadas de desempenho que vão além do processamento incremental básico (foco na funcionalidade e correção).
- Implementação de jobs adicionais além da sincronização do vault (e.g., refresco de embeddings de conceitos).

## Critérios de Aceitação
- Serviço `clarifai-scheduler` adicionado ao monorepo, com seu Dockerfile e configurado para execução.
- `APScheduler` configurado para executar jobs em horários programados (e.g., cron job diário).
- Job `sync_vault_to_graph()` implementado e funcional:
    - Lê corretamente todos os arquivos Markdown Tier 1 (e outros tiers com `clarifai:id` se incluídos).
    - Calcula o hash do conteúdo visível para cada bloco com `clarifai:id` de forma consistente.
    - Compara corretamente o hash calculado com o hash armazenado no Neo4j.
    - Atualiza as propriedades dos nós no Neo4j (`text`, `hash`, `last_updated`) e marca-os como dirty (`needs_reprocessing: true`) e incrementa a versão (`ver=`) quando o conteúdo Markdown é alterado.
- Logging detalhado implementado para rastreabilidade e diagnóstico do job.
- Contêiner Docker configurado e funcional para o serviço `clarifai-scheduler`.
- Documentação clara do serviço e do job de sincronização.
- Testes demonstrando a funcionalidade do job de sincronização, incluindo cenários de blocos inalterados, alterados e novos/removidos.

## Dependências
- Docker Compose stack configurado (de Sprint 1), incluindo `clarifai-scheduler` e `neo4j`.
- Neo4j configurado e acessível (de Sprint 1).
- Estrutura de arquivos Markdown Tier 1 (e possivelmente outros tiers) com `clarifai:id` e `^anchor` definida e existente no vault (de Sprint 2).
- Definição clara do formato de blocos com `clarifai:id` e `ver=` (conforme `on-graph_vault_synchronization.md`).

## Entregáveis
- Código-fonte do serviço `clarifai-scheduler` (incluindo o `Dockerfile`).
- Implementação do job `sync_vault_to_graph()`.
- Configuração do `APScheduler` para o job.
- Documentação do serviço e do job de sincronização.
- Testes unitários e de integração para o job de sincronização.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Falhas na sincronização causando inconsistências entre o vault e o grafo.
  - **Mitigação**: Implementar verificações de integridade pós-sincronização (e.g., contagens de nós/blocos, comparação de hashes para amostras); logging detalhado para identificar o ponto exato da falha; implementar um mecanismo de "dry run" para testes.
- **Risco**: Problemas de desempenho com grandes volumes de arquivos ou muitos blocos.
  - **Mitigação**: Implementar processamento incremental (apenas blocos modificados/novos); otimizar as consultas Neo4j para comparação de hashes; considerar processamento em lote para atualizações no Neo4j.
- **Risco**: Conflitos de acesso a arquivos durante a leitura/hash por outros processos (e.g., Obsidian).
  - **Mitigação**: O `on-filehandle_conflicts.md` já descreve que o Obsidian não usa locks exclusivos para leitura. O scheduler deve apenas ler os arquivos. Para leituras, a probabilidade de um problema é baixa, mas robustecer com retries em caso de erro de leitura de I/O.

## Notas Técnicas
- Utilizar `APScheduler` para gerenciamento de jobs cron pela sua simplicidade e capacidade de execução em contêineres Docker.
- A estratégia de hash para detecção de alterações deve focar no `semantic_text` do bloco (o texto visível, excluindo os comentários `clarifai:id`), para garantir que apenas alterações de conteúdo real acionem o reprocessamento. Referência: `on-refreshing_concept_embeddings.md`.
- A atualização dos nós no Neo4j deve incluir o incremento da propriedade `ver=` (versão) e a marcação de `needs_reprocessing: true` para que o pipeline Claimify saiba quais blocos precisam ser reprocessados.
- Estruturar logs de forma clara para facilitar diagnóstico de problemas, incluindo IDs dos blocos processados e o status (inalterado, alterado, erro).
- Considerar uma arquitetura de processamento em "batch" para as interações com o Neo4j (ex: `UNWIND` para múltiplos `MERGE`/`SET`) para otimizar a performance de atualização do grafo.
- Implementar mecanismos básicos de recuperação de falhas para o job (e.g., retries simples para erros de DB ou I/O).
