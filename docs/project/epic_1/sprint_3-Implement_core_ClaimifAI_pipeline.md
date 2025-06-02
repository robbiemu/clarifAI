# Tarefa: Implementar componentes principais do pipeline Claimify

## Descrição
Desenvolver e implementar os componentes principais do pipeline Claimify, incluindo as etapas de Selection, Disambiguation e Decomposition, para extrair claims de alta qualidade a partir de **chunks de enunciados Tier 1**.

## Escopo

### Incluído
- Implementação do componente de **Selection (Seleção)** para identificar `chunks de enunciados` que contêm informações verificáveis e são relevantes para claims.
- Desenvolvimento do componente de **Disambiguation (Desambiguação)** para reescrever sentenças, remover ambiguidades e adicionar sujeitos inferidos, transformando referências (`e.g., "it"`) em entidades concretas.
- Criação do componente de **Decomposition (Decomposição)** para quebrar as sentenças desambiguadas em **claims atômicos, auto-contidos e independentes** que atendam aos critérios de Claimify (`on-claim_generation.md`).
- Configuração para processar **cada chunk de enunciado individualmente**, fornecendo o contexto de janela (`p` sentenças anteriores, `f` sentenças seguintes) conforme configurado e especificado em `on-graph_vault_synchronization.md` (Context Window for Claimify Processing).
- Estruturar o pipeline para **permitir a injeção** de modelos de linguagem (LLMs) específicos para cada etapa (Selection, Disambiguation, Decomposition), **preparando para a futura configurabilidade** conforme `design_config_panel.md`.
- Estruturação da saída de cada etapa para facilitar a avaliação de qualidade posterior e a ingestão no grafo. Claims que não passam na Decomposition por não serem auto-contidos devem ser tratados como `(:Sentence)` nodes no grafo.
- Implementação de logging e rastreabilidade detalhada do processo Claimify.
- Documentação detalhada da arquitetura e funcionamento do pipeline Claimify.

### Excluído
- Interface de usuário para visualização do processo (será tratada em sprints posteriores).
- Avaliação de qualidade dos claims (scores de `entailed_score`, `coverage_score`, `decontextualization_score`) que será implementada em sprint posterior (Sprint 7).
- Vinculação de claims a conceitos (será implementada em sprint posterior, Sprint 5).
- Persistência final dos claims como arquivos Markdown (será feita após a avaliação de qualidade).
- Otimizações avançadas de desempenho ou processamento em lote de grandes volumes de dados (foco na funcionalidade e correção do pipeline).

## Critérios de Aceitação
- Pipeline completo implementado com os três componentes funcionais: Selection, Disambiguation e Decomposition.
- Cada componente processa corretamente seu input e gera output no formato estruturado esperado.
- O componente de Selection identifica sentenças relevantes e as passa para a próxima etapa.
- O componente de Disambiguation produz sentenças reescritas, removendo ambiguidades e adicionando contexto quando possível.
- O componente de Decomposition gera apenas claims que são **atômicos, auto-contidos e verificáveis**, e **descarta (ou marca como `(:Sentence)` nodes)** os que não atendem a esses critérios.
- O processamento de cada etapa respeita a **janela de contexto (`p` e `f`)** conforme a configuração do sistema.
- O pipeline é projetado para **aceitar diferentes instâncias de modelos de linguagem** para cada etapa, demonstrando a capacidade de ser configurado futuramente (e.g., por meio de parâmetros de função ou injeção de dependência), alinhado com `design_config_panel.md`.
- Saída estruturada de claims e sentenças para facilitar avaliação de qualidade e ingestão no grafo (`(:Claim)` ou `(:Sentence)` nodes).
- Logging detalhado do processo, incluindo as decisões ou transformações tomadas em cada etapa (e.g., quais sentenças foram selecionadas, como foram desambiguadas, quais claims foram decompostos e quais foram descartados na Decomposition).
- Documentação clara da arquitetura e funcionamento do pipeline.
- Testes unitários e de integração demonstrando a funcionalidade e a qualidade da saída em cenários variados.

## Dependências
- Acesso a modelos de linguagem (LLMs).
- Sistema de segmentação de texto (chunks de enunciados) implementado e funcional (de Sprint 2).
- Definição clara do formato de entrada (`chunks de enunciados`) e saída para cada componente (conforme `on-claim_generation.md`).
- Definição da estrutura e dos parâmetros de configuração para modelos e janelas (`p`, `f`) (conforme `design_config_panel.md`), que guiarão a **implementação da interface** para esses modelos.

## Entregáveis
- Código-fonte dos componentes do pipeline Claimify (Selection, Disambiguation, Decomposition).
- Lógica para passar o contexto de janela (`p`, `f`) para os prompts dos LLMs.
- Configuração de exemplos para modelos de linguagem.
- Documentação técnica detalhada da arquitetura e funcionamento do pipeline Claimify.
- Testes unitários e de integração com casos de uso variados, incluindo exemplos de `on-claim_generation.md`.
- Exemplos de processamento e saída de cada etapa do pipeline.

## Estimativa de Esforço
- 5 dias de trabalho

## Riscos e Mitigações
- **Risco**: Qualidade inconsistente dos claims extraídos (e.g., claims não atômicos, ainda ambíguos).
  - **Mitigação**: Iteração constante nos prompts dos LLMs; implementação de testes de regressão com exemplos "golden standard"; e refinamento dos critérios de aceitação para a fase de Decomposition (e.g., verificar auto-contenção via NLI ou LLM).
- **Risco**: Desempenho inadequado ou latência elevada com textos mais longos ou complexos.
  - **Mitigação**: Monitorar o tempo de resposta do LLM para cada etapa; otimizar o tamanho dos prompts; considerar o uso de modelos LLM mais eficientes para etapas que não exigem a inteligência máxima (conforme `design_config_panel.md`).
- **Risco**: Consumo excessivo de tokens LLM.
  - **Mitigação**: Otimizar o design dos prompts para serem concisos; implementar estratégias de caching para resultados de LLM; e garantir que apenas o contexto de janela *necessário* (`p`, `f`) seja enviado ao LLM.

## Notas Técnicas
- Utilizar prompts cuidadosamente projetados para cada etapa do pipeline Claimify, instruindo o LLM sobre o formato e os critérios de saída.
- Implementar a lógica para passar o contexto de janela (`p` e `f`) para os prompts dos LLMs de forma eficiente, extraindo as sentenças vizinhas do conjunto de `chunks de enunciados` previamente gerados.
- Ao codificar, considerar a **abstração da interface LLM** para que diferentes modelos possam ser facilmente "plugados" em cada etapa (e.g., usando uma classe base ou interface de LLM), facilitando a integração futura com as opções de configuração.
- Implementar um sistema de cache (e.g., simples cache de memória ou Redis) para evitar reprocessamento de chunks de enunciados idênticos.
- Estruturar o código de forma modular, com funções claras para Selection, Disambiguation e Decomposition, facilitando a manutenção, testabilidade e extensão futura.
- Documentar claramente os requisitos e limitações de cada componente do pipeline, especialmente em relação ao tipo de texto que melhor processam.