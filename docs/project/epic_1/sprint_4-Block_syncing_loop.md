# Tarefa: Sincronização de Blocos Alterados: Atualizar Nós do Grafo e Marcar para Reprocessamento

## Descrição
Implementar o loop de sincronização que recebe notificações do `vault-watcher` sobre blocos Markdown alterados, realiza a validação de versão, atualiza os nós correspondentes no Neo4j com o novo conteúdo e incrementa a versão, e marca esses nós para reprocessamento pelo pipeline Claimify.

## Escopo

### Incluído
- **Consumo de Notificações de Blocos Alterados:** Implementar um **consumidor de mensagens** dentro do `aclarai-core` (ou um componente dedicado) que se conecte ao RabbitMQ e escute por mensagens na fila (e.g., `aclarai_dirty_blocks`) publicadas pelo `vault-watcher`. Cada mensagem conterá o `aclarai:id` do bloco e o `file_path` do arquivo Markdown modificado.
- **Leitura e Parsing de Blocos:** Para cada bloco notificado via mensagem, ler seu conteúdo atual do arquivo Markdown e parsear o texto visível (`semantic_text`) e a versão (`ver=`).
- **Lógica de Verificação de Versão e Otimistic Locking (`on-graph_vault_synchronization.md`):**
    - Recuperar a versão (`ver=`) do nó correspondente no Neo4j.
    - Comparar a versão do vault com a versão do grafo:
        - **Se `vault_ver == graph_ver`:** Considerar uma atualização limpa.
        - **Se `vault_ver > graph_ver`:** Proceder com a atualização (vault é mais recente).
        - **Se `vault_ver < graph_ver`:** **Detectar conflito.** Pular a atualização deste bloco no grafo e registrar o conflito para diagnóstico, conforme `on-graph_vault_synchronization.md` ("Conflict Detection").
- **Atualização de Nós no Grafo:**
    - Para blocos que passaram na verificação de versão, atualizar o nó `(:Block)` (ou `(:Claim)`, `(:Concept)` dependendo do tier) no Neo4j com o novo `text` e o hash do `semantic_text`.
    - **Incrementar a propriedade `ver=` (versão) do nó no Neo4j** (`ver = ver + 1`).
- **Marcação para Reprocessamento:** Marcar os nós atualizados no Neo4j com uma flag como `needs_reprocessing: true` para indicar que eles precisam ser processados novamente pelo pipeline Claimify e outros agentes.
- **Integração com `vault-watcher`:** Garantir que o `aclarai-core` possa receber as notificações do `vault-watcher` via RabbitMQ.
- Documentação detalhada da lógica de sincronização de blocos e do fluxo de atualização.
- Implementação de testes para verificar a correta atualização de nós, o controle de versão e o tratamento de conflitos.

### Excluído
- A lógica de detecção de alterações nos arquivos Markdown (responsabilidade do `vault-watcher` de Sprint 4).
- O processamento real dos blocos marcados como `needs_reprocessing: true` pelo pipeline Claimify ou outros agentes (isso acontecerá em etapas posteriores, orquestrado pelo `scheduler`).
- Geração de novos nós ou relacionamentos para blocos *novos* (isso é parte do job `sync_vault_to_graph` em Sprint 3).
- Resolução *automática* de conflitos complexos (e.g., merge de conteúdo em caso de `vault_ver < graph_ver`).
- Interface de usuário para visualização do status de sincronização de blocos.
- Otimizações avançadas de desempenho que vão além da eficiência das consultas e atualizações no Neo4j.

## Critérios de Aceitação
- O sistema consome corretamente as notificações de blocos alterados do `vault-watcher`.
- Para cada bloco notificado, o conteúdo é lido e parseado corretamente.
- A lógica de verificação de versão (`vault_ver` vs `graph_ver`) é implementada com precisão, incluindo a detecção de conflitos.
- Nós existentes no grafo são atualizados corretamente com o novo conteúdo e a propriedade `ver=` é incrementada quando uma alteração limpa é detectada.
- Nós atualizados são marcados com `needs_reprocessing: true` no Neo4j.
- Conflitos de versão (`vault_ver < graph_ver`) são detectados, a atualização é pulada para o bloco em conflito e o evento é logado.
- A integração com o `vault-watcher` é funcional e robusta.
- Documentação clara e precisa da lógica de sincronização de blocos, incluindo o fluxo de versão e tratamento de conflitos.
- Testes automatizados demonstram a funcionalidade e robustez, cobrindo cenários de: bloco inalterado, bloco alterado (vault mais recente), e conflito de versão (grafo mais recente).

## Dependências
- `vault-watcher` implementado e funcional (de Sprint 4), notificando blocos alterados.
- Estrutura de nós `(:Block)`, `(:Claim)`, `(:Sentence)`, `(:Concept)` no Neo4j com propriedades `text`, `hash`, `ver=` definidas (de Sprint 3 e 5).
- Acesso ao Neo4j para consultas e atualizações de nós.
- Acesso ao sistema de arquivos para ler o conteúdo dos blocos Markdown.
- Definição detalhada da lógica de sincronização e controle de versão em `on-graph_vault_synchronization.md`.

## Entregáveis
- Código-fonte para o componente responsável pela sincronização de blocos alterados no `aclarai-core` (ou serviço dedicado).
- Implementação da lógica de verificação de versão e atualização de nós no Neo4j.
- Lógica para marcar nós como `needs_reprocessing: true`.
- Documentação técnica detalhada do fluxo de sincronização de blocos, incluindo controle de versão e tratamento de conflitos.
- Testes unitários e de integração focados na lógica de sincronização de blocos.

## Estimativa de Esforço
- 2 dias de trabalho (dado que o `vault-watcher` e `sync_vault_to_graph` já abordam partes).

## Riscos e Mitigações
- **Risco**: Lógica de verificação de versão ou tratamento de conflitos implementada incorretamente, levando a perda de dados ou inconsistências.
  - **Mitigação**: Testes extensivos, especialmente para cenários de conflito; revisão de código focada na lógica de controle de versão; seguir rigorosamente as especificações de `on-graph_vault_synchronization.md`.
- **Risco**: Desempenho inadequado ao processar um grande número de blocos alterados rapidamente.
  - **Mitigação**: Otimizar as consultas Cypher para atualização de nós; considerar a ingestão em lote de atualizações no Neo4j; implementar um mecanismo de fila interna se o `vault-watcher` notificar blocos muito rapidamente.
- **Risco**: Dados incompletos ou corrompidos sendo lidos dos arquivos Markdown no momento da atualização.
  - **Mitigação**: Embora o `vault-watcher` já lide com a detecção, esta camada deve ter resiliência (e.g., retries para I/O errors) ao ler os arquivos; garantir que a escrita atômica do aclarai para o vault previna leituras de arquivos parciais.

## Notas Técnicas
- O foco desta tarefa é a lógica de **atualização de blocos existentes** no grafo devido a alterações no vault, e não a criação de novos blocos (que é coberta pelo `sync_vault_to_graph` de Sprint 3).
- Implementar a lógica de `Block Diffing` para comparar o conteúdo do bloco Markdown com o que está no grafo, e a lógica de `Change Types` para determinar a ação apropriada (`update`, `skip conflict`).
- A propriedade `ver=` deve ser um contador incremental robusto para cada bloco.
- Usar transações no Neo4j para garantir a atomicidade das atualizações de nós.
- A flag `needs_reprocessing: true` é crucial para orquestrar o re-processamento por Claimify e outros agentes no `scheduler` em sprints futuras.
- O componente que implementa esta lógica deve ser parte do `aclarai-core` ou um módulo de sincronização dentro dele, pois precisa acessar o grafo e os arquivos.
