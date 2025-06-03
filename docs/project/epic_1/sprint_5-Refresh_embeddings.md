# Tarefa: Atualizar embeddings de arquivos de conceito diariamente

## Descrição
Implementar um job agendado para atualizar periodicamente os embeddings dos arquivos de conceito, garantindo que as representações vetoriais reflitam o conteúdo atual dos arquivos Markdown Tier 3 e mantendo a consistência entre o vault e o índice vetorial.

## Escopo

### Incluído
- Implementação de um job agendado (utilizando o `APScheduler` já configurado em Sprint 3) para atualizar embeddings de arquivos de conceito.
- Desenvolvimento de lógica para **detectar alterações em arquivos de conceito** (`vault/concepts/*.md`):
    - Para cada arquivo de conceito, extrair o `semantic_text` (conteúdo visível, removendo metadados `clarifai:id` e `^anchor`, conforme `on-refreshing_concept_embeddings.md`).
    - Calcular o SHA256 `embedding_hash` do `semantic_text`.
    - Comparar este hash com o `c.embedding_hash` armazenado no `(:Concept)` node correspondente no Neo4j.
    - Se os hashes forem diferentes, ou se o `embedding_hash` no Neo4j for `null`, o arquivo é considerado modificado e precisa de atualização.
- **Recálculo de embeddings para arquivos modificados**:
    - Chamar o modelo de embedding configurado (de Sprint 2) para gerar um novo vetor para o `semantic_text` modificado.
- **Atualização do índice vetorial e metadados no Neo4j**:
    - **Upsert** o novo embedding para o conceito no `concepts` vector store (conforme `on-vector_stores.md`).
    - Atualizar o `(:Concept)` node correspondente no Neo4j, definindo `c.embedding_hash` para o novo hash calculado e `c.last_updated` para a data/hora atual (conforme `on-concepts.md` e `on-refreshing_concept_embeddings.md`).
- Implementação de logging detalhado para o início, término, e resultado da execução do job, incluindo o número de conceitos processados e atualizados.
- Documentação do sistema e seu funcionamento.
- Implementação de testes para verificar a correta atualização.

### Excluído
- Interface de usuário para visualização do status de atualização.
- Otimizações avançadas de desempenho que vão além do processamento incremental básico.
- Treinamento de modelos de embedding personalizados (foco no uso de modelos existentes).
- Processamento em lote de grandes volumes de dados que excedam a capacidade de uma execução diária incremental.
- Análise avançada de drift semântico ou sugestão de fusão/divisão de conceitos (isso é escopo de tarefas futuras, esta foca na atualização da representação).

## Critérios de Aceitação
- Job agendado executa diariamente (ou conforme cron configurado) para atualizar embeddings.
- O sistema detecta corretamente alterações em arquivos de conceito utilizando o hashing do `semantic_text`.
- Embeddings são recalculados com precisão para arquivos modificados.
- O `concepts` vector store é atualizado (`upsert`) com os novos embeddings.
- Os `(:Concept)` nodes no Neo4j têm suas propriedades `embedding_hash` e `last_updated` corretamente atualizadas.
- Logging detalhado do processo é implementado, indicando quais conceitos foram atualizados e por quê.
- Documentação clara do sistema e seu funcionamento interno.
- Testes automatizados demonstram funcionalidade e robustez, incluindo cenários de arquivo inalterado, arquivo modificado, e `null` `embedding_hash` inicial.

## Dependências
- Sistema de agendamento de jobs (`clarifai-scheduler` com `APScheduler`) implementado e funcional (de Sprint 3).
- Sistema de conceitos implementado (incluindo `(:Concept)` nodes no Neo4j e o `concepts` vector store populado, de tarefas anteriores desta Sprint 5).
- Modelo de embedding configurado e acessível (de Sprint 2).
- Acesso ao Neo4j para atualização de metadados.
- Acesso ao `concepts` vector store para atualização de embeddings.
- Definição clara do processo de atualização de embeddings em `on-refreshing_concept_embeddings.md`.

## Entregáveis
- Código-fonte do job de atualização de embeddings (dentro do serviço `clarifai-scheduler`).
- Implementação da lógica de detecção de alterações (hashing) e recálculo de embeddings.
- Documentação do sistema e seu funcionamento.
- Testes unitários e de integração.
- Logs de execução e relatórios de status para o job.

## Estimativa de Esforço
- **5 dias de trabalho**

## Riscos e Mitigações
- **Risco**: Falhas na detecção de alterações em arquivos devido a variações de formatação ou metadados não-semânticos.
  - **Mitigação**: Implementar a função `strip_metadata` de forma robusta e testá-la com diversas variações de arquivos Markdown. A dependência do `semantic_text` é crucial aqui.
- **Risco**: Desempenho inadequado com um grande número de conceitos ou arquivos de conceito muito grandes.
  - **Mitigação**: A atualização é incremental (apenas para modificados). Otimizar a leitura de arquivos e chamadas ao serviço de embedding (e.g., processamento em lote se o serviço permitir).
- **Risco**: Inconsistências entre embeddings e conteúdo atual (e.g., embedding incorreto, atualização falha).
  - **Mitigação**: Implementar verificações de integridade pós-atualização (e.g., re-verificar o hash no Neo4j após a operação); logging detalhado para identificar o ponto exato da falha; implementar um mecanismo de retry para operações de DB/embedding.

## Notas Técnicas
- A lógica de detecção de alterações deve seguir rigorosamente o método de hashing do `semantic_text` conforme detalhado em `on-refreshing_concept_embeddings.md`.
- O job deve ser resiliente a erros (e.g., arquivo não encontrado, erro de conexão com DB/embedding service) e registrar falhas sem interromper a execução para outros conceitos.
- Considerar o uso de transações no Neo4j para garantir a atomicidade das atualizações de nós.
- A integração com o `APScheduler` deve ser limpa, registrando o job de forma que ele possa ser facilmente habilitado/desabilitado ou configurado via cron (preparando para Sprint 6).
