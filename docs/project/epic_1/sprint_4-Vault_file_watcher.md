# Tarefa: Implementar observador de arquivos do vault com detecção de blocos modificados

## Descrição
Desenvolver um sistema de observação de arquivos (`vault-watcher`) que monitore alterações nos arquivos Markdown do vault e detecte blocos modificados (com base em `clarifai:id` e `ver=`), permitindo a sinalização para sincronização eficiente entre o vault e o grafo de conhecimento.

## Escopo

### Incluído
- Implementação de um sistema de observação de arquivos (usando uma biblioteca como `watchdog` para Python) que monitore alterações em arquivos `.md` nos diretórios configurados do vault (Tier 1, 2, 3).
- Desenvolvimento de lógica para detectar blocos modificados (dirty blocks) por meio de `Block Diffing` (`on-graph_vault_synchronization.md`):
    - Parsing do conteúdo dos arquivos Markdown para identificar `clarifai:id` e `ver=` dos blocos.
    - Comparação do conteúdo (hash do texto visível) e da versão (`ver=`) dos blocos entre o estado anterior (em memória ou no grafo) e o novo estado.
- Implementação de parsing de Markdown para identificação precisa de blocos e seus metadados `clarifai:id`.
- Criação de um sistema de notificação (e.g., uma fila interna ou um evento de pub/sub) para alterações detectadas, indicando quais blocos foram modificados.
- Integração com o sistema de sincronização existente (o job `sync_vault_to_graph` de Sprint 3) para sinalizar a necessidade de reprocessamento para blocos dirty.
- Documentação do sistema `vault-watcher` e seu funcionamento.
- Implementação de testes para verificar a correta detecção de alterações (criação, modificação, exclusão) e o parsing de blocos.

### Excluído
- Interface de usuário para visualização em tempo real de alterações ou notificação explícita de usuário.
- O reprocessamento automático completo dos blocos dirty (isso é função do job de sincronização e do pipeline Claimify, não do watcher em si).
- Otimizações avançadas de desempenho para cenários de vault extremamente grandes (milhões de arquivos).
- Resolução de conflitos complexos de versão além da detecção de `version mismatch`.

## Critérios de Aceitação
- Sistema `vault-watcher` observa corretamente alterações em arquivos `.md` nas pastas configuradas do vault.
- Blocos modificados são detectados com precisão com base no `clarifai:id` e no hash do conteúdo visível.
- O parsing de Markdown funciona corretamente para identificação e extração de `clarifai:id` e `ver=` dos blocos.
- O sistema de notificação informa adequadamente sobre as alterações detectadas (quais blocos são dirty).
- A integração com o job de sincronização sinaliza corretamente quais blocos precisam ser reprocessados.
- Documentação clara do sistema `vault-watcher` e seu funcionamento interno.
- Testes automatizados demonstrando a funcionalidade e robustez do watcher em cenários de criação, modificação e exclusão de arquivos e blocos.

## Dependências
- Estrutura de arquivos Markdown com comentários `clarifai:id` e `ver=` definida e presente no vault (`idea-creating_tier1_documents.md`, `on-graph_vault_synchronization.md`).
- Job de sincronização `sync_vault_to_graph()` implementado (de Sprint 3), que consumirá as notificações do watcher.
- Acesso ao sistema de arquivos para monitoramento (`vault-watcher` roda como um serviço separado).
- O monorepo já configurado com o serviço `vault-watcher` (de Sprint 1).

## Entregáveis
- Código-fonte do serviço `vault-watcher` (incluindo `Dockerfile`).
- Implementação da lógica de detecção de blocos modificados (`Block Diffing`).
- Sistema de notificação (e.g., módulo Python de eventos internos ou API para o scheduler).
- Documentação do sistema `vault-watcher` e seu funcionamento interno.
- Testes unitários e de integração para o `vault-watcher`.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Falhas na detecção de alterações em formatos de arquivo Markdown complexos ou com variações de formatação.
  - **Mitigação**: Implementar parsing robusto para lidar com diferentes estilos de Markdown e comentários HTML; realizar testes com diversos formatos e layouts de blocos.
- **Risco**: Sobrecarga do sistema ou consumo excessivo de recursos com muitas alterações simultâneas (e.g., durante um pull de git grande).
  - **Mitigação**: Implementar *batching* e *throttling* de eventos de arquivo (e.g., processar eventos a cada X segundos ou após Y eventos); otimizar o algoritmo de `Block Diffing` para ser eficiente.
- **Risco**: Perda de eventos de alteração em determinadas condições (e.g., sistema sobrecarregado, queda do watcher).
  - **Mitigação**: A sincronização periódica completa (`sync_vault_to_graph` agendada via cron) atua como um fallback, garantindo que o grafo eventualmente reflita o estado do vault, mitigando a perda de eventos em tempo real. Além disso, implementar logging robusto para eventos perdidos.

## Notas Técnicas
- Utilizar bibliotecas de monitoramento de sistema de arquivos como `watchdog` (Python) pela sua eficiência e suporte a diferentes sistemas operacionais.
- Implementar *batching* de eventos para evitar a sobrecarga de processamento quando muitas alterações ocorrem rapidamente.
- A detecção de alterações deve se basear na comparação do hash do conteúdo visível do bloco e na propriedade `ver=` (versão) para identificar `dirty blocks` com precisão.
- Estruturar o `vault-watcher` como um serviço de longa duração, rodando em seu próprio contêiner Docker.
- A notificação de blocos `dirty` deve ser uma comunicação eficiente com o `clarifai-core` ou diretamente com o job `sync_vault_to_graph`.
- Implementar logging detalhado para diagnóstico de problemas, incluindo quais arquivos e blocos estão sendo monitorados e quais alterações foram detectadas.
