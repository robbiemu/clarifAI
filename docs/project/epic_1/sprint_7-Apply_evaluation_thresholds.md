# Tarefa: Aplicar Limiares de Avaliação para Vinculação e Filtragem

## Descrição
Implementar um sistema para aplicar limiares de avaliação na vinculação de conceitos e na filtragem de claims. Este sistema utilizará as pontuações de qualidade dos claims (`entailed_score`, `coverage_score`, `decontextualization_score`) para determinar quais claims devem ser vinculados a conceitos, promovidos para o conhecimento base do usuário (Tier 2/3 Markdown) ou incluídos em resumos. A lógica seguirá o método de média geométrica e as regras de filtragem definidas em `docs/arch/on-evaluation_agents.md` e `docs/project/technical_overview.md`.

## Escopo

### Incluído
- Implementação do **cálculo da média geométrica** a partir das três pontuações de avaliação de um claim (`entailed_score`, `coverage_score`, `decontextualization_score`), conforme a fórmula em `docs/arch/on-evaluation_agents.md` (Seção "Scoring Interpretation").
- Desenvolvimento de **lógica centralizada de filtragem** que:
    - Verifica se todas as três pontuações (`entailed_score`, `coverage_score`, `decontextualization_score`) são **não-nulas**. Se qualquer uma for `null`, o claim é imediatamente excluído do processamento downstream (conforme `docs/arch/on-evaluation_agents.md`, "Scoring Interpretation").
    - Compara a média geométrica calculada com um **limiar de qualidade do sistema** (configurável via `docs/arch/design_config_panel.md`, Seção 2 "Thresholds & Parameters").
- Aplicação desses limiares e da lógica de filtragem nas seguintes operações:
    - **Vinculação de Conceitos:** Apenas claims que atendem aos critérios de qualidade (não-nulos e média geométrica ≥ limiar) podem ser vinculados a conceitos via `SUPPORTS_CONCEPT` ou `CONTRADICTS_CONCEPT` (conforme `docs/arch/on-linking_claims_to_concepts.md` e `docs/project/technical_overview.md`, Seção IV.C "Edge Creation Rules & Confidence Weighting"). Claims que não atendem aos critérios, mas ainda mencionam um conceito, podem ser vinculados via `MENTIONS_CONCEPT`.
    - **Promoção de Claims:** Claims que atendem aos critérios de qualidade são considerados para inclusão em arquivos Markdown Tier 2 e Tier 3 (conforme `docs/arch/on-evaluation_agents.md`, "Promotion Logic").
    - **Inclusão em Resumos:** Apenas claims que atendem aos critérios de qualidade são utilizados pelos agentes de resumo para gerar conteúdo Tier 2 e Tier 3 (conforme `docs/arch/on-writing_vault_documents.md`).
- Integração da lógica de filtragem com os pipelines existentes de claim-to-concept (Sprint 5) e atualização do vault (Sprint 3 e 4).
- Documentação clara do processo de aplicação de limiares, incluindo a fórmula da média geométrica, as regras de filtragem e seus efeitos no fluxo de dados.
- Implementação de testes para verificar o correto funcionamento da média geométrica e da lógica de filtragem em diversos cenários (claims de alta/baixa qualidade, com/sem `null` scores).

### Excluído
- Interface de usuário para ajuste *dinâmico* de limiares em tempo real que não seja através do arquivo `clarifai.config.yaml` ou da UI de configuração já planejada (de Sprint 6).
- Otimizações avançadas de desempenho que não são inerentes à lógica de filtragem em si.
- Algoritmos complexos de ponderação adaptativa para as pontuações (a média geométrica é fixa).
- Análise estatística avançada de distribuição de pontuações.

## Critérios de Aceitação
- O sistema calcula corretamente a média geométrica a partir das três pontuações de avaliação de um claim.
- A lógica de filtragem verifica corretamente a presença de `null` scores e, se presentes, exclui o claim do processamento downstream relevante.
- Claims com média geométrica abaixo do limiar configurado são filtrados apropriadamente, não sendo vinculados a conceitos (exceto `MENTIONS_CONCEPT`), promovidos ou incluídos em resumos.
- A integração da lógica de filtragem com as operações de vinculação de conceitos, promoção de claims e inclusão em resumos funciona corretamente.
- A documentação clara do processo de aplicação de limiares e seus efeitos está disponível.
- Testes automatizados demonstram a funcionalidade e robustez da lógica de filtragem, cobrindo cenários de sucesso e diferentes tipos de falha/qualidade.

## Dependências
- Agentes de avaliação de `entailment`, `coverage` e `decontextualization` implementados (tarefas anteriores deste Sprint 7), populando as pontuações nos `(:Claim)` nodes e arestas.
- Sistema de vinculação de conceitos implementado (de Sprint 5), que será modificado para respeitar os limiares.
- Sistema de geração de resumos implementado (de Sprint 3 e 4), que será modificado para respeitar os limiares.
- Acesso ao Neo4j para consulta das pontuações dos claims.
- Configuração dos limiares de qualidade no `clarifai.config.yaml` (de Sprint 6).

## Entregáveis
- Código-fonte do sistema de aplicação de limiares (módulo dentro do `clarifai-core`).
- Implementação da lógica de cálculo da média geométrica.
- Modificações nos pipelines de vinculação de conceitos, promoção de claims e geração de resumos para incorporar a lógica de filtragem.
- Documentação do processo e seus efeitos.
- Testes unitários e de integração para a lógica de filtragem.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Limiares muito restritivos filtrando claims válidos e úteis, resultando em um grafo de conhecimento muito escasso.
  - **Mitigação**: Implementar calibração inicial cuidadosa dos limiares com base em uma amostra representativa de claims e avaliações humanas. A documentação deve enfatizar a importância da calibração.
- **Risco**: Limiares muito permissivos permitindo claims de baixa qualidade entrarem no grafo, poluindo o conhecimento base.
  - **Mitigação**: Monitorar a qualidade dos claims resultantes no grafo e ajustar os limiares conforme necessário. A capacidade de visualizar o grafo (em sprints futuras) ajudará nessa validação.
- **Risco**: Inconsistência na aplicação de filtros entre diferentes componentes ou pipelines.
  - **Mitigação**: Centralizar a lógica de filtragem em um único módulo ou função que todos os componentes downstream devem chamar. Garantir que os testes cubram a aplicação consistente dos filtros em todos os pontos de uso.

## Notas Técnicas
- A média geométrica é a métrica de escolha para balancear os diferentes aspectos de qualidade (`docs/arch/on-evaluation_agents.md`).
- O tratamento de `null` scores é crucial: qualquer `null` score deve automaticamente desqualificar o claim para promoção ou vinculação forte, sem a necessidade de calcular a média geométrica.
- O logging detalhado das decisões de filtragem (claim aceito/rejeitado e por quê) será fundamental para a depuração e calibração dos limiares.
- A lógica de filtragem deve ser flexível o suficiente para permitir ajustes futuros nos limiares através do arquivo de configuração.
- A aplicação desta lógica deve ser feita nos pontos onde os claims são "consumidos" para fins de vinculação, promoção ou sumarização.
