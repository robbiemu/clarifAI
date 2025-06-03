# Tarefa: Aprimorar resumos Tier 2 para incluir conceitos vinculados

## Descrição
Aprimorar o sistema de resumos Tier 2 para incluir links para conceitos relevantes, permitindo uma navegação mais rica entre resumos e conceitos relacionados no grafo de conhecimento. Isso implica que **claims (nós `:Claim`) já precisam estar vinculados a conceitos (nós `:Concept`) no grafo Neo4j antes desta tarefa**.

## Escopo

### Incluído
- Implementação de lógica para **identificar, para cada bloco de resumo Tier 2**, os `(:Claim)` nodes que estão relacionados a ele (`:SUMMARIZED_IN` edge) e que, por sua vez, estão vinculados a `(:Concept)` nodes (via `SUPPORTS_CONCEPT`, `MENTIONS_CONCEPT`, etc.).
- Desenvolvimento de lógica para **incorporar links `[[Concept Name]]` inline** no Markdown dos arquivos Tier 2 onde os conceitos são mencionados ou suportados pelos claims resumidos, conforme o formato de `on-writing_vault_documents.md` (seção "Tier 2 Summary Agent", Notas).
- Integração com o sistema de conceitos existente (que já contém os `(:Concept)` nodes).
- Atualização do processo de geração/reprocessamento de resumos (do Sprint 3) para incluir esta nova etapa de vinculação de conceitos.
- Reutilização da **escrita atômica para arquivos Markdown** (implementada em Sprint 3) para a atualização dos arquivos Tier 2.
- Documentação do processo e do formato atualizado dos resumos Tier 2.
- Implementação de testes para verificar a correta vinculação de conceitos e a integridade dos links no Markdown.

### Excluído
- Criação de conceitos ou do `(:Concept)` node no Neo4j (implementado em tarefa separada, Sprint 5).
- Criação de relacionamentos `SUPPORTS_CONCEPT` ou `MENTIONS_CONCEPT` (implementado em tarefa separada, Sprint 5).
- Interface de usuário para visualização ou gerenciamento de conceitos.
- Otimizações avançadas de desempenho que vão além de consultas eficientes ao Neo4j.
- Vinculação bidirecional de `[[Concept]]` para `[[Summary]]` (e.g., footers nos arquivos de conceito), que será implementada em tarefa separada (Sprint 5).
- Processamento em lote de grandes volumes de dados (foco na atualização incremental).

## Critérios de Aceitação
- Sistema escaneia corretamente cada bloco de resumo para identificar os claims que o compõem e os conceitos vinculados a esses claims no grafo.
- Links `[[Concept Name]]` são incorporados inline de forma precisa e contextualizada no Markdown Tier 2, seguindo o formato de wikilinks do Obsidian.
- A integração com o sistema de conceitos e o grafo Neo4j funciona corretamente para recuperar os nomes dos conceitos e seus relacionamentos.
- O processo de geração/atualização de resumos Tier 2 é aprimorado para incluir a vinculação automática de conceitos.
- Documentação clara e atualizada do processo e do formato dos resumos Tier 2 aprimorados.
- Testes automatizados demonstram a funcionalidade de adição de links de conceitos e a robustez da atualização dos arquivos Markdown.
- Cada bloco de resumo Tier 2 gerado inclui seus próprios marcadores clarifai:id e ver= e ^anchor.

## Dependências
- Sistema de resumos Tier 2 implementado (de Sprint 3), que gera os blocos de resumo.
- Sistema de conceitos **existente no grafo** (ou seja, `(:Concept)` nodes já existem), o que aponta para uma dependência de Sprint 5 para a *criação* desses nós e dos relacionamentos.
- Relacionamentos `SUPPORTS_CONCEPT` e `MENTIONS_CONCEPT` **já definidos e populados no grafo** entre `(:Claim)` e `(:Concept)` nodes (também de Sprint 5).
- Acesso ao sistema de arquivos para atualização de arquivos Markdown (e a lógica de escrita atômica já implementada em Sprint 3).
- Definição clara do formato de resumo Tier 2 com links de conceito (`on-writing_vault_documents.md`).

## Entregáveis
- Código-fonte atualizado para o sistema de geração de resumos Tier 2 (`clarifai-core`).
- Implementação da lógica de escaneamento e vinculação de conceitos a partir do grafo.
- Documentação do processo e formato atualizado dos resumos Tier 2.
- Testes unitários e de integração para a funcionalidade de vinculação de conceitos.
- Exemplos de arquivos de resumo Tier 2 gerados com links funcionais para conceitos.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Vinculação excessiva ou irrelevante de conceitos, poluindo os resumos.
  - **Mitigação**: Implementar critérios de relevância (e.g., apenas vincular conceitos de claims com `strength` acima de um threshold, ou limitar o número de links por resumo); considerar uma lógica para evitar repetição de links para o mesmo conceito em um curto espaço no resumo.
- **Risco**: Links quebrados para conceitos inexistentes (nomes de arquivos errados, IDs não encontrados).
  - **Mitigação**: Implementar verificação da existência do conceito no grafo antes de gerar o wikilink; garantir que os nomes dos arquivos de conceito (`[[Concept Name]]`) gerados sejam canônicos e consistentes com os nomes dos nós `(:Concept)`.
- **Risco**: Desempenho inadequado ao consultar o grafo para relacionamentos de conceitos para cada resumo.
  - **Mitigação**: Otimizar consultas Cypher para serem eficientes (e.g., usar `MATCH` e `WHERE` eficientemente, garantir índices); implementar caching de resultados de consultas de conceitos para reduzir a carga no Neo4j.

## Notas Técnicas
- Utilizar consultas Cypher eficientes para identificar os `(:Concept)` nodes vinculados aos `(:Claim)` nodes que compõem o resumo.
- A lógica deve focar em transformar os nomes de conceitos em `[[wikilinks]]` Markdown.
- **Esta tarefa tem uma dependência cruzada com a tarefa de Sprint 5 "Link claims to concepts with SUPPORTS_CONCEPT, MENTIONS_CONCEPT, etc." e "Create/update Tier 3 Markdown files and (:Concept) nodes." O ideal é que esta tarefa só comece *após* a conclusão das partes relevantes de Sprint 5 que criam os conceitos e seus links aos claims.**
- Manter a consistência na formatação dos links e nomes dos conceitos para facilitar o processamento futuro e a interoperabilidade com o Obsidian.
- A lógica deve ser resiliente a cenários onde não há conceitos vinculados a um resumo.
