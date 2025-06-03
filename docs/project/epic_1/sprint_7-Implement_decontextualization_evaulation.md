# Tarefa: Implementar Agente de Avaliação de Descontextualização

## Descrição
Desenvolver e implementar um agente de avaliação de descontextualização que analise o quanto um claim pode ser compreendido independentemente de seu contexto original (source), produzindo uma pontuação (`decontextualization_score`) que indique o grau de autonomia semântica do claim. Esta pontuação é fundamental para garantir que os claims promovidos para o conhecimento base sejam portáteis e compreensíveis por si só, conforme detalhado em `docs/arch/on-evaluation_agents.md` e `docs/project/technical_overview.md`.

## Escopo

### Incluído
- Implementação do **Agente de Avaliação de Descontextualização**, seguindo a descrição em `docs/arch/on-evaluation_agents.md` (Seção "Agent: `decontextualization`").
- Desenvolvimento de lógica para analisar o `claim` (texto do claim candidato) e sua `source` (bloco Markdown original ou contexto estruturado), produzindo um `decontextualization_score` (float entre 0.0 e 1.0). A estrutura de entrada para o agente é definida em `docs/arch/on-evaluation_agents.md` (Seção "Input Format").
- Armazenamento da pontuação `decontextualization_score` como uma propriedade na aresta `[:ORIGINATES_FROM]` que conecta o `(:Claim)` node ao seu `(:Block)` de origem no Neo4j, conforme `docs/arch/on-evaluation_agents.md` (Seção "Storage").
- Armazenamento da pontuação `decontextualization_score` como metadado em um comentário HTML no Markdown Tier 1 (`<!-- clarifai:decontextualization_score=0.88 -->`), conforme `docs/arch/on-evaluation_agents.md` (Seção "Storage").
- Implementação de um sistema de retry robusto para o agente em casos de falha (e.g., timeout, erro do LLM), consistente com o tratamento de falhas de outros agentes de avaliação (conforme `docs/arch/on-evaluation_agents.md`, Seção "Failure Handling").
- Tratamento adequado de valores `null` para `decontextualization_score` em caso de falha do agente após os retries. Claims com scores `null` não serão escritos em Markdown nem vinculados a conceitos (conforme `docs/arch/on-evaluation_agents.md`, Seção "Failure Handling").
- Documentação clara do processo de avaliação, incluindo a estrutura do prompt, a saída esperada e a interpretação das pontuações.
- Implementação de testes para verificar a correta avaliação do `decontextualization_score` em diversos cenários (claims auto-contidos, claims com referências implícitas, etc.).

### Excluído
- Interface de usuário para visualização *direta* das pontuações (isso será coberto em Sprint 8).
- Otimizações avançadas de desempenho que vão além de um sistema de retry eficiente e o uso de prompts otimizados.
- Treinamento de modelos personalizados para avaliação de descontextualização (foco no uso de LLMs configuráveis, conforme `docs/arch/on-evaluation_agents.md`, Seção "Model Configuration").
- Processamento em lote de volumes *extremamente* grandes de dados (foco na funcionalidade e correção).
- Integração com sistemas externos de análise de linguagem (o LLM é a fonte principal de avaliação).

## Critérios de Aceitação
- O Agente de Descontextualização está implementado e determina corretamente o `decontextualization_score` a partir do claim e da source.
- A pontuação `decontextualization_score` é armazenada corretamente na aresta `[:ORIGINATES_FROM]` no grafo Neo4j e como metadado no Markdown Tier 1.
- O sistema de retry funciona adequadamente para casos de falha do agente, com o `decontextualization_score` sendo definido como `null` após falhas persistentes.
- O tratamento de valores `null` está apropriado, garantindo que claims com `null` score não sejam processados downstream (no que diz respeito a serem escritos em Markdown ou vinculados a conceitos *nesta fase*).
- A documentação clara do processo de avaliação de descontextualização, incluindo a estrutura do prompt e a interpretação da pontuação, está disponível.
- Testes automatizados demonstram a funcionalidade e robustez do agente, incluindo casos de sucesso e falha.

## Dependências
- Pipeline Claimify implementado (de Sprint 3), fornecendo claims e suas fontes.
- Nós `(:Claim)` e `(:Block)` e arestas `[:ORIGINATES_FROM]` criados no Neo4j (de Sprint 3), para armazenamento das pontuações.
- Acesso ao sistema de arquivos para atualização de metadados Markdown Tier 1.
- Modelo de linguagem (LLM) configurado para avaliação (conforme `docs/arch/design_config_panel.md` e `docs/arch/on-evaluation_agents.md`, Seção "Model Configuration").
- Mecanismos de escrita atômica para arquivos Markdown (de Sprint 3).

## Entregáveis
- Código-fonte do Agente de Avaliação de Descontextualização.
- Lógica para armazenamento de pontuações na aresta `[:ORIGINATES_FROM]` no Neo4j e em metadados Markdown.
- Implementação do sistema de retry e tratamento de `null` values para o score.
- Documentação detalhada do processo de avaliação de descontextualização.
- Testes unitários e de integração para o agente de avaliação.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Subjetividade na avaliação de descontextualização pelo LLM.
  - **Mitigação**: Estabelecer critérios claros e exemplos de referência (few-shot examples) no prompt para guiar o LLM, conforme `docs/arch/on-evaluation_agents.md`. Realizar calibração e testes de regressão com um conjunto de dados anotado.
- **Risco**: Falhas frequentes no processamento do LLM, resultando em muitos scores `null`.
  - **Mitigação**: Implementar um sistema robusto de retry com backoff exponencial. Monitorar as taxas de falha do LLM e ajustar o modelo ou o tamanho/complexidade do prompt.
- **Risco**: Pontuações numéricas produzidas pelo LLM não refletem adequadamente a autonomia semântica real.
  - **Mitigação**: Validar a correlação das pontuações do LLM com uma amostra de avaliações manuais (humanas) e ajustar o prompt ou o mapeamento de saída do LLM para a escala de 0-1 conforme necessário.

## Notas Técnicas
- O `decontextualization_score` deve ser um `Float` que pode ser `null` no Neo4j e no Markdown, conforme `docs/arch/on-evaluation_agents.md`.
- A estrutura do prompt para o LLM deve ser otimizada para a tarefa de descontextualização, conforme o exemplo em `docs/arch/on-evaluation_agents.md` (Seção "Prompt").
- O agente deve ser capaz de receber o modelo LLM a ser utilizado via configuração (do Sprint 6).
- A escrita dos metadados no Markdown deve ser feita utilizando a lógica de escrita atômica já existente para garantir a segurança dos arquivos.
- O logging deve incluir o `claim_id` e o `source_id` para facilitar a depuração e rastreabilidade.
