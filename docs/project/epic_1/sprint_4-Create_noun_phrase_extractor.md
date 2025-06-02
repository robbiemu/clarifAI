# Tarefa: Criar extrator de frases nominais em claims + resumos

## Descrição
Desenvolver um sistema para extrair frases nominais (noun phrases) de claims (`(:Claim)` nodes) e resumos (`(:Summary)` nodes) do grafo, normalizá-las, incorporá-las (embedding) e armazená-las na tabela `concept_candidates`. Esta tabela servirá como **input de dados para a tarefa subsequente de detecção de conceitos baseada em `hnswlib` (neste mesmo Sprint 4).**

## Escopo

### Incluído
- Implementação de um sistema para buscar `(:Claim)` e `(:Summary)` nodes do grafo Neo4j.
- Desenvolvimento de extrator de frases nominais utilizando **`spaCy` (`doc.noun_chunks`)** a partir do `text` de cada nó, conforme especificado em `on-noun_phrase_extraction.md`.
- Implementação de normalização de frases nominais: **minúsculas, lematização de substantivos, remoção de pontuação e trimming de espaços em branco** (`on-concepts.md`, item 1.2).
- **Incorporação (embedding)** de cada frase nominal normalizada usando o sistema de embeddings configurado (de Sprint 2).
- Armazenamento de cada frase nominal normalizada e seu embedding na tabela `concept_candidates` do vector store, com metadados essenciais (`on-concepts.md`, seção "concept_candidates Vector Table`).
- Marcação de cada entrada na tabela `concept_candidates` com um status inicial de `"pending"` para futura desduplicação e promoção.
- Documentação do sistema extrator de frases nominais e seu funcionamento.
- Implementação de testes para verificar a correta extração, normalização, embedding e armazenamento de frases nominais.

### Excluído
- Interface de usuário para visualização de frases nominais extraídas.
- Desduplicação e promoção de conceitos (será implementada na tarefa subsequente de Sprint 4 "Usar hnswlib para detecção de conceitos baseada em embeddings", que **consumirá o output desta tarefa**).
- Otimizações avançadas de desempenho que vão além de consultas eficientes e processamento em lote.
- Treinamento ou fine-tuning de modelos personalizados para extração de frases (foco no uso de modelos spaCy off-the-shelf).
- Processamento em lote de grandes volumes de dados (foco na ingestão incremental de claims/resumos novos ou alterados).

## Critérios de Aceitação
- Sistema busca corretamente `(:Claim)` e `(:Summary)` nodes do grafo Neo4j.
- O extrator de frases nominais utilizando `spaCy` (`doc.noun_chunks`) funciona com precisão, extraindo frases relevantes do texto dos nós.
- Frases nominais são normalizadas adequadamente (minúsculas, lematização, remoção de pontuação e trimming de espaços em branco).
- Cada frase nominal normalizada é incorporada (embedding) e armazenada corretamente na tabela `concept_candidates` do vector store.
- Cada entrada na tabela `concept_candidates` é marcada com o status `"pending"`.
- Metadados essenciais (`text`, `embedding`, `source_claim_id`, `clarifai:id`, `status`) são armazenados corretamente na tabela `concept_candidates`.
- Documentação clara do sistema de extração de frases nominais e seu funcionamento.
- Testes automatizados demonstram a funcionalidade e robustez da extração, normalização, embedding e armazenamento de frases nominais.

## Dependências
- Neo4j configurado com nós `(:Claim)` e `(:Summary)` populados (de Sprint 3).
- `spaCy` instalado com modelo apropriado (e.g., `en_core_web_sm` ou `en_core_web_trf`), conforme `on-noun_phrase_extraction.md`.
- Sistema de embeddings configurado e funcional (de Sprint 2), para gerar os vetores das frases nominais.
- Tabela de vetores `concept_candidates` inicializada (parte da configuração do vector store, geralmente em Sprint 2/1).

## Entregáveis
- Código-fonte do extrator de frases nominais (componente dentro de `clarifai-core`).
- Implementação da lógica de normalização e armazenamento na tabela `concept_candidates`.
- Documentação técnica do sistema e seu funcionamento.
- Testes unitários e de integração para todas as etapas da extração e persistência.
- Exemplos de frases nominais extraídas, normalizadas e armazenadas.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Qualidade inconsistente na extração de frases nominais (e.g., extração de ruído, frases incompletas).
  - **Mitigação**: Testar diferentes modelos `spaCy` e ajustar seus componentes ou configurar regras personalizadas para filtragem de ruído (`on-noun_phrase_extraction.md`); implementar filtros pós-extração baseados em tamanho ou tipo de token.
- **Risco**: Excesso de frases nominais irrelevantes sendo armazenadas, sobrecarregando o `concept_candidates` ou o pipeline subsequente.
  - **Mitigação**: Implementar filtros de relevância baseados em frequência, comprimento mínimo/máximo de palavras, ou remoção de stopwords muito comuns; considerar um threshold de frequência mínima antes de adicionar a `concept_candidates`.
- **Risco**: Desempenho inadequado com grande volume de claims/resumos a serem processados.
  - **Mitigação**: Implementar processamento em lotes (`batch processing`) para consultas ao grafo e para processamento com `spaCy`; otimizar as consultas ao Neo4j para buscar os claims/resumos.

## Notas Técnicas
- Utilizar os modelos `spaCy` apropriados para o idioma (`en_core_web_sm` ou `en_core_web_trf`) e a complexidade do texto, conforme a recomendação em `on-noun_phrase_extraction.md`.
- A normalização deve ser rigorosa para maximizar a chance de detecção de duplicatas por similaridade.
- Assegurar que os metadados corretos (`source_claim_id`, `clarifai:id` para rastreabilidade) sejam armazenados junto com a frase e o embedding na tabela `concept_candidates`, conforme `on-concepts.md`.
- Este componente deve ser acionado sempre que novos `(:Claim)` ou `(:Summary)` nodes forem criados ou alterados no grafo.
- Implementar mecanismos de recuperação de falhas durante o processamento do `spaCy` ou a persistência na tabela de vetores.
