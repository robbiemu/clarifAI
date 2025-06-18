# Tarefa: Usar `hnswlib` para detecção de conceitos baseada em embeddings

## Descrição
Implementar um sistema de detecção de conceitos baseado em embeddings utilizando a biblioteca `hnswlib`. Este sistema permitirá a **identificação lógica de conceitos semânticos similares e a determinação de seu status (promovido ou mesclado)**, utilizando a tabela `concept_candidates` como fonte de vetores. A **população completa** desta tabela será realizada em um sprint posterior.

## Escopo

### Incluído
- Inicialização e gerenciamento de um **índice `hnswlib`** utilizando os vetores que serão armazenados na tabela `concept_candidates`.
- Implementação da **lógica central para detectar conceitos similares (candidatos a duplicatas)**:
    - Para cada candidato a conceito, consultar o índice `hnswlib` para itens semanticamente similares (`nearest neighbors`).
    - Avaliar a similaridade usando **distância de cosseno** (ou outra métrica apropriada para embeddings) contra um `threshold` configurável (e.g., `0.90` conforme `design_config_panel.md`).
- Desenvolvimento de sistema para **determinar o status de promoção ou fusão de candidatos:**
    - **Se uma correspondência (`match`) for encontrada** acima do `threshold` de similaridade: A lógica deve identificar o conceito `(:Concept)` existente no Neo4j ao qual o candidato se vincula e/ou determinar que o candidato na tabela `concept_candidates` deve ser marcado como `"merged"`.
    - **Se nenhuma correspondência for encontrada** acima do `threshold`: A lógica deve determinar que o candidato é um novo conceito potencial e deve ser marcado para **"promoção"** (`"promoted"`).
- Integração da lógica de detecção com o pipeline de processamento de conceitos (`aclarai-core`), onde os candidatos serão eventualmente gerados e processados por este sistema.
- Documentação do sistema `hnswlib`, da lógica de detecção de similaridade e de como as decisões de promoção/fusão são tomadas.
- Implementação de testes unitários e de integração para verificar a **correta funcionalidade da lógica de detecção e classificação de similaridade**, utilizando um conjunto de dados de teste **mock ou pre-populado minimamente** na tabela `concept_candidates`.

### Excluído
- A população *completa e contínua* da tabela `concept_candidates` com frases nominais (este é o escopo da tarefa de Sprint 4 "Criar extrator de frases nominais em claims + resumos").
- A criação efetiva dos `(:Concept)` nodes no Neo4j ou dos arquivos Markdown Tier 3 a partir de candidatos "promovidos" (isso será feito em Sprint 5).
- A vinculação de claims a conceitos ou a atualização de `last_seen` e `aliases` em `(:Concept)` nodes existentes.
- Interface de usuário para visualização ou sugestão interativa de conceitos similares.
- Otimizações avançadas de desempenho que vão além da configuração ideal do `hnswlib` e do processamento em lote.
- Treinamento ou fine-tuning de modelos de embedding personalizados (foco no uso de modelos existentes).
- Clustering avançado de conceitos (além da detecção de vizinhos mais próximos para deduplicação).

## Critérios de Aceitação
- O índice `hnswlib` é inicializado corretamente com os vetores disponíveis no armazenamento `concept_candidates` (mesmo que minimamente populado para testes).
- O sistema implementa e testa a lógica de detecção de candidatos a duplicatas de conceitos com precisão, utilizando o `threshold` de similaridade configurável.
- A lógica para determinar se um candidato é "merged" (se similaridade > threshold) ou "promoted" (se não há similaridade suficiente) é implementada e testada.
- A integração da lógica de detecção com o pipeline de processamento de conceitos (`aclarai-core`) funciona corretamente.
- Documentação clara e precisa do sistema de detecção de conceitos baseado em `hnswlib` e da lógica de decisão.
- Testes automatizados demonstram a **correta funcionalidade da lógica de similaridade e classificação de status**, cobrindo cenários de duplicação exata, similaridade próxima e conceitos totalmente novos, utilizando um conjunto de dados de teste controlado.

## Dependências
- Armazenamento de vetores `concept_candidates` implementado (de Sprint 4, onde a tabela é criada).
- Sistema de embeddings configurado e funcional (de Sprint 2), para gerar os vetores que estarão na tabela `concept_candidates`.
- Pipeline de processamento de conceitos (dentro de `aclarai-core`) que eventualmente usará este módulo.
- Definição da estratégia de conceitos em `on-concepts.md` (especialmente 1.3 e 1.4).

## Entregáveis
- Código-fonte do componente de detecção de conceitos baseado em `hnswlib` (dentro de `aclarai-core`).
- Implementação da inicialização e da lógica de consulta do índice `hnswlib`.
- Lógica para determinar o status "merged" ou "promoted" de candidatos a conceitos.
- Documentação técnica do sistema `hnswlib` e da lógica de detecção.
- Testes unitários e de integração para a lógica de detecção de similaridade, usando dados de teste **mock ou mínimos**.

## Estimativa de Esforço
- 8 dias de trabalho

## Riscos e Mitigações
- **Risco**: Falsos positivos (conceitos distintos marcados como similares) ou falsos negativos (conceitos similares não detectados) na detecção de similaridade.
  - **Mitigação**: Ajustar cuidadosamente o `threshold` de similaridade; implementar testes de regressão com exemplos "golden standard" de pares similares/distintos; considerar a possibilidade de uma "verificação secundária" para casos de similaridade limítrofe (e.g., um LLM, se necessário, em sprints futuras).
- **Risco**: Desempenho inadequado do `hnswlib` com grande volume de dados ou alta dimensionalidade de embeddings.
  - **Mitigação**: Otimizar os parâmetros do `hnswlib` (`M`, `ef_construction`, `ef_search`) para equilibrar precisão e velocidade; considerar estratégias de indexação em lote e de persistência do índice para evitar reconstrução completa a cada reinício.
- **Risco**: Qualidade inconsistente de embeddings impactando a precisão da similaridade.
  - **Mitigação**: Embora o modelo de embedding seja uma dependência, esta tarefa deve incluir testes que validem a *capacidade* do `hnswlib` de operar com a qualidade de embedding fornecida; reportar e colaborar com o time de embeddings se a qualidade for um problema.

## Notas Técnicas
- Utilizar os parâmetros apropriados para o índice `hnswlib` (`M`, `ef_construction`, `ef_search`) para otimizar o trade-off entre precisão e velocidade. A escolha desses parâmetros depende da dimensionalidade dos embeddings e do número de itens.
- A métrica de distância deve ser de cosseno (`cosine_distance`) se os embeddings são otimizados para essa métrica (o que é comum para Sentence Transformers e embeddings de LLMs).
- Implementar estratégias de processamento em lote (`batch processing`) para indexação e consulta de grandes volumes de candidatos.
- A persistência do índice `hnswlib` em disco deve ser considerada para evitar reconstrução completa a cada ciclo, melhorando o desempenho.
- O sistema deve lidar com o armazenamento de metadados adicionais na tabela `concept_candidates` (`status`, `source_claim_id`, etc.) para facilitar a rastreabilidade e análise posterior.
- O output deste componente é primariamente uma **decisão lógica** sobre o status de um candidato (promovido ou mesclado), que então será utilizada pela tarefa de Sprint 5 para a criação/atualização dos nós `(:Concept)` no Neo4j.
