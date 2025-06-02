# Tarefa: Criar nós (:Claim) e (:Sentence) no Neo4j

## Descrição
Implementar a criação e gerenciamento de nós `(:Claim)` e `(:Sentence)` no banco de dados Neo4j, estabelecendo a estrutura fundamental do grafo de conhecimento para armazenar e relacionar claims extraídos e sentenças originais, incluindo as propriedades de qualidade dos claims e o relacionamento `ORIGINATES_FROM`.

## Escopo

### Incluído
- Definição do esquema para nós `(:Claim)` e `(:Sentence)` no Neo4j, conforme especificado em `technical_overview.md` (seção IV.A `Claim` Node Properties).
- Implementação de funções para criar nós `(:Claim)` a partir de claims extraídos pelo pipeline Claimify, incluindo as propriedades `entailed_score`, `coverage_score`, e `decontextualization_score` (que podem ser `null` neste sprint).
- Implementação de funções para criar nós `(:Sentence)` para chunks de enunciados que não geraram claims de alta qualidade (e.g., foram descartados na fase de Decomposition do Claimify ou marcados como ambíguos), incluindo a propriedade `ambiguous` se aplicável.
- Estabelecimento do relacionamento `(:Claim)-[:ORIGINATES_FROM]->(:Block)` ou `(:Sentence)-[:ORIGINATES_FROM]->(:Block)` para conectar claims e sentenças aos seus blocos de origem Tier 1 (`technical_overview.md` e `on-graph_vault_synchronization.md`).
- Armazenamento de metadados relevantes para ambos os tipos de nós (e.g., `clarifai:id`, `text`, `version`, `timestamp`).
- Implementação de índices apropriados para propriedades frequentemente consultadas (e.g., `clarifai:id`, `text`).
- Documentação do esquema e uso da API de interação com o Neo4j.

### Excluído
- Interface de usuário para visualização do grafo.
- Implementação de relacionamentos com conceitos (e.g., `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`) que será feito em Sprint 5.
- Avaliação de qualidade dos claims no pipeline Claimify (o cálculo dos scores), pois os scores virão da tarefa anterior deste sprint (mas a persistência dos scores `null` ou preenchidos já é incluída).
- Otimizações avançadas de consulta (além dos índices básicos).
- Migração de dados legados.

## Critérios de Aceitação
- Esquema de nós `(:Claim)` (com `entailed_score`, `coverage_score`, `decontextualization_score`) e `(:Sentence)` (com `ambiguous` opcional) definido e documentado.
- Funções para criar nós `(:Claim)` a partir da saída do Claimify implementadas e testadas.
- Funções para criar nós `(:Sentence)` a partir de chunks de enunciados que não resultaram em claims implementadas e testadas.
- Relacionamento `ORIGINATES_FROM` entre claims/sentenças e seus blocos de origem estabelecido corretamente no grafo.
- Metadados relevantes (`clarifai:id`, `text`, `version`, `timestamp`, scores de qualidade) armazenados adequadamente em cada nó.
- Índices criados no Neo4j para propriedades-chave (`clarifai:id`, `text`) para consultas eficientes.
- Documentação clara do esquema do grafo e das funções da API.
- Testes unitários e de integração demonstrando a funcionalidade de criação e persistência de nós e relacionamentos no Neo4j.

## Dependências
- Neo4j configurado e acessível (de Sprint 1).
- Pipeline Claimify implementado para extração de claims e identificação de sentenças que não viraram claims (da tarefa anterior deste sprint).
- Definição clara do formato de saída dos claims e sentenças do pipeline Claimify.
- Definição do esquema de nós e relacionamentos em `technical_overview.md`.

## Entregáveis
- Código-fonte para criação e gerenciamento de nós `(:Claim)` e `(:Sentence)` no Neo4j (via LlamaIndex ou driver direto).
- Esquema documentado do grafo, incluindo propriedades e relacionamentos.
- Funções de API (internas do serviço `clarifai-core`) para interação com o grafo.
- Testes unitários e de integração.
- Documentação de uso e exemplos de dados criados.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Esquema inadequado para necessidades futuras ou para a captura completa da semântica de Claimify.
  - **Mitigação**: Projetar o esquema com base em `technical_overview.md`, permitindo extensibilidade futura (e.g., adicionar mais propriedades ou rótulos sem refatoração drástica); documentar claramente as convenções e princípios de design.
- **Risco**: Desempenho inadequado com grande volume de dados ou alta taxa de ingestão.
  - **Mitigação**: Implementar índices apropriados desde o início; considerar estratégias de ingestão em lote (batching) para criação de nós e relacionamentos; monitorar o desempenho durante os testes.
- **Risco**: Inconsistências entre o grafo e os dados de origem (e.g., blocos Markdown).
  - **Mitigação**: Focar na precisão dos `clarifai:id` e versionamento. Os mecanismos de sincronização (`vault-to-graph sync` de Sprint 3 e `file watcher` de Sprint 4) mitigarão isso a longo prazo.

## Notas Técnicas
- Utilizar o LlamaIndex (`KnowledgeGraphIndex` ou `Neo4jGraphStore`) para abstrair a interação com o Neo4j, se o LlamaIndex suportar a criação de nós com propriedades complexas e relacionamentos arbitrários. Caso contrário, usar o driver Neo4j Python diretamente.
- Implementar as propriedades `entailed_score`, `coverage_score`, e `decontextualization_score` como `Float` (ou `null` se não avaliadas) para `(:Claim)` nós.
- Criar a propriedade `ambiguous` (Boolean) para nós `(:Sentence)` quando apropriado.
- Priorizar a criação do relacionamento `ORIGINATES_FROM` para garantir a rastreabilidade imediata dos claims e sentenças.
- Implementar índices no Neo4j para propriedades frequentemente consultadas, especialmente `clarifai:id` para buscas rápidas.
- Considerar estratégias de processamento em lote (Cypher `UNWIND` para múltiplos `CREATE` ou `MERGE`) para otimizar a performance de ingestão.
- Documentar claramente as convenções de nomenclatura para nós (`:Claim`, `:Sentence`, `:Block`) e relacionamentos (`:ORIGINATES_FROM`).
