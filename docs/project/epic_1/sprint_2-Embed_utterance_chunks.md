# Tarefa: Incorporar chunks de enunciados e armazenar vetores no Postgres via LlamaIndex

## Descrição
Implementar um sistema para segmentar blocos Markdown Tier 1 em chunks coerentes, incorporá-los usando modelos de embedding e armazenar os vetores resultantes no Postgres utilizando a integração pgvector do LlamaIndex, permitindo pesquisas de similaridade eficientes.

## Escopo

### Incluído
- Implementação de segmentação de blocos Markdown Tier 1 usando **`SentenceSplitter` do LlamaIndex** para criar chunks coerentes, seguindo a estratégia definida em `on-sentence_splitting.md`.
- Configuração e uso de modelos de embedding configuráveis (definidos via `.env`, por exemplo, modelos BERT-based como Sentence Transformers).
- Armazenamento de vetores resultantes no Postgres usando a integração `PGVectorStore` do LlamaIndex, na tabela `utterances`.
- Inclusão de metadados essenciais no armazenamento de vetores: `clarifai:id` (referência ao bloco Markdown pai), `chunk_index` (índice ordinal do chunk dentro do bloco), e o texto original do chunk.
- Implementação de indexação eficiente para consultas de similaridade no Postgres, utilizando o índice `ivfflat` do `pgvector`.
- Documentação do processo de embedding e armazenamento.
- Testes de funcionalidade e desempenho.

### Excluído
- Interface de usuário para visualização de embeddings
- Otimização avançada de consultas vetoriais
- Implementação de clustering ou redução de dimensionalidade
- Migração de dados legados
- Implementação de sistemas de cache complexos

## Critérios de Aceitação
- TextSplitter do LlamaIndex configurado e segmentando blocos Markdown em chunks coerentes
- Modelo de embedding configurável gerando vetores de qualidade
- Vetores armazenados corretamente no Postgres com extensão pgvector
- Metadados essenciais (clarifai:id, chunk_index, texto original) preservados
- Consultas de similaridade funcionando com desempenho aceitável
- Documentação clara sobre o processo e configuração
- Testes demonstrando funcionalidade e desempenho

## Dependências
- Postgres com extensão pgvector instalada e configurada
- Acesso a modelos de embedding
- Sistema de blocos Markdown Tier 1 implementado
- LlamaIndex instalado e configurado

## Entregáveis
- Código-fonte para segmentação, embedding e armazenamento
- Configuração do Postgres com pgvector
- Documentação do processo e uso
- Testes de funcionalidade e desempenho
- Exemplos de consultas de similaridade

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Desempenho inadequado com grande volume de dados
  - **Mitigação**: Implementar indexação eficiente e monitorar desempenho
- **Risco**: Qualidade inconsistente de embeddings
  - **Mitigação**: Testar diferentes modelos e parâmetros de segmentação
- **Risco**: Problemas de compatibilidade com versões do Postgres/pgvector
  - **Mitigação**: Fixar versões específicas e documentar requisitos

## Notas Técnicas
- Utilizar TextSplitter do LlamaIndex com parâmetros adequados para o domínio
- Considerar o uso de chunk_size e chunk_overlap apropriados para o contexto
- Implementar indexação IVF (Inverted File Index) para consultas eficientes
- Armazenar metadados suficientes para rastreabilidade completa
- Considerar estratégias de batch processing para grandes volumes de dados
- Avaliar diferentes modelos de embedding para qualidade vs. desempenho
