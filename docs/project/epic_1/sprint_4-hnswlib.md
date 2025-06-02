# Tarefa: Usar `hnswlib` para detecção de conceitos baseada em embeddings

## Descrição
Implementar um sistema de detecção de conceitos baseado em embeddings utilizando a biblioteca `hnswlib`, permitindo a identificação eficiente de conceitos semânticos similares e a prevenção de duplicatas no grafo de conhecimento (`(:Concept)` nodes no Neo4j), utilizando o `concept_candidates` vector table como fonte.

## Escopo

### Incluído
- Inicialização e gerenciamento de um **índice `hnswlib`** utilizando os vetores armazenados na tabela `concept_candidates` (de Sprint 4).
- Implementação de lógica para **detectar conceitos similares (candidatos a duplicatas)**:
    - Para cada novo candidato a conceito (ou a cada ciclo de revalidação), consultar o índice `hnswlib` para itens semanticamente similares (`nearest neighbors`).
    - Avaliar a similaridade usando **distância de cosseno** (ou outra métrica apropriada para embeddings) contra um `threshold` configurável (e.g., `0.90` conforme `design_config_panel.md`).
- Desenvolvimento de sistema para **promover ou mesclar candidatos:**
    - **Se uma correspondência (`match`) for encontrada** acima do `threshold` de similaridade: Vincular o candidato ao conceito `(:Concept)` existente no Neo4j e/ou marcar o candidato na tabela `concept_candidates` como `"merged"` (`on-concepts.md`, item 1.4, 2.2).
    - **Se nenhuma correspondência for encontrada** acima do `threshold`: O candidato é considerado um novo conceito potencial e marcado para **"promoção"** (`"promoted"`) para se tornar um novo `(:Concept)` node no Neo4j (`on-concepts.md`, item 1.4).
- Integração com o pipeline de processamento de conceitos (`clarifai-core`), onde os candidatos são gerados e depois processados por este sistema de detecção.
- Documentação do sistema `hnswlib` e seu funcionamento dentro do pipeline de conceitos.
- Implementação de testes para verificar a correta detecção de similaridade e o fluxo de promoção/fusão.

### Excluído
- Interface de usuário para visualização ou sugestão interativa de conceitos similares.
- Otimizações avançadas de desempenho que vão além da configuração ideal do `hnswlib` e do processamento em lote.
- Treinamento ou fine-tuning de modelos de embedding personalizados (foco no uso de modelos existentes).
- O processo de extração de noun phrases e a criação dos `concept_candidates` (isso é uma dependência de Sprint 5).
- A criação efetiva dos `(:Concept)` nodes no Neo4j ou dos arquivos Markdown Tier 3 (isso será feito em Sprint 5).
- Clustering avançado de conceitos (além da detecção de vizinhos mais próximos para deduplicação).

## Critérios de Aceitação
- O índice `hnswlib` é inicializado corretamente com os vetores do armazenamento `concept_candidates`.
- O sistema detecta candidatos a duplicatas de conceitos com precisão, utilizando o `threshold` de similaridade configurável.
- Candidatos são corretamente identificados como "merged" (se similaridade > threshold) ou "promoted" (se não há similaridade suficiente) na tabela `concept_candidates`.
- A lógica de vinculação a conceitos existentes ou de promoção de novos conceitos é implementada e testada.
- A integração com o pipeline de processamento de conceitos (`clarifai-core`) funciona corretamente, recebendo candidatos e aplicando a lógica de detecção.
- Documentação clara e precisa do sistema de detecção de conceitos baseado em `hnswlib`.
- Testes automatizados demonstram a funcionalidade e robustez, cobrindo cenários de duplicação exata, similaridade próxima e conceitos totalmente novos.

## Dependências
- Armazenamento de vetores `concept_candidates` implementado (de Sprint 4), populado com noun phrases e seus embeddings.
- Sistema de embeddings configurado e funcional (de Sprint 2), para gerar os vetores dos `concept_candidates`.
- Pipeline de processamento de conceitos (dentro de `clarifai-core`) que gera os `concept_candidates` e consumirá os resultados deste módulo.
- Definição da estratégia de conceitos em `on-concepts.md`.

## Entregáveis
- Código-fonte do componente de detecção de conceitos baseado em `hnswlib` (dentro de `clarifai-core`).
- Implementação da inicialização e consulta do índice `hnswlib`.
- Lógica de marcação de candidatos como "merged" ou "promoted" na tabela `concept_candidates`.
- Documentação técnica do sistema e seu funcionamento.
- Testes unitários e de integração para a detecção de similaridade.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Falsos positivos (conceitos distintos marcados como similares) ou falsos negativos (conceitos similares não detectados) na detecção de similaridade.
  - **Mitigação**: Ajustar cuidadosamente o `threshold` de similaridade; implementar testes de regressão com exemplos "golden standard" de pares similares/distintos; considerar a possibilidade de uma "verificação secundária" para casos de similaridade limítrofe (e.g., um LLM, se necessário, em sprints futuras).
- **Risco**: Desempenho inadequado do `hnswlib` com grande volume de dados ou alta dimensionalidade de embeddings.
  - **Mitigação**: Otimizar os parâmetros do `hnswlib` (`M`, `ef_construction`, `ef_search`) para equilibrar precisão e velocidade; implementar estratégias de indexação em lote e de persistência do índice para evitar reconstrução completa a cada reinício.
- **Risco**: Qualidade inconsistente de embeddings impactando a precisão da similaridade.
  - **Mitigação**: Embora o modelo de embedding seja uma dependência, esta tarefa deve incluir testes que validem a *capacidade* do `hnswlib` de operar com a qualidade de embedding fornecida; reportar e colaborar com o time de embeddings se a qualidade for um problema.

## Notas Técnicas
- Utilizar os parâmetros apropriados para o índice `hnswlib` (`M`, `ef_construction`, `ef_search`) para otimizar o trade-off entre precisão e velocidade. A escolha desses parâmetros depende da dimensionalidade dos embeddings e do número de itens.
- **A métrica de distância deve ser de cosseno** (`cosine_distance`) se os embeddings são otimizados para essa métrica (o que é comum para Sentence Transformers e embeddings de LLMs).
- Implementar estratégias de processamento em lote (`batch processing`) para indexação e consulta de grandes volumes de candidatos.
- A persistência do índice `hnswlib` em disco deve ser considerada para evitar reconstrução completa a cada ciclo, melhorando o desempenho.
- O sistema deve lidar com o armazenamento de metadados adicionais na tabela `concept_candidates` (`status`, `source_claim_id`, etc.) para facilitar a rastreabilidade e análise posterior.
- O output deste componente é primariamente uma **decisão** sobre o status de um candidato (promovido ou mesclado), que então será utilizada pela tarefa de Sprint 5 para a criação/atualização dos nós `(:Concept)` no Neo4j.
