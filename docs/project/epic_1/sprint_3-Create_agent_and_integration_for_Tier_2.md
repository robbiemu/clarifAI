# Tarefa: Criar o agente e integração para gerar resumos Tier 2 com links de volta para Tier 1

## Descrição
Desenvolver um agente inteligente e sua integração para gerar resumos Tier 2 a partir de conteúdo Tier 1 (especificamente dos `(:Claim)` nodes de alta qualidade), incluindo links de volta para os blocos originais do Tier 1, garantindo rastreabilidade e navegação eficiente entre os níveis de informação. O processo de escrita para o vault deve ser atômico.

## Escopo

### Incluído
- Implementação do **Tier 2 Summary Agent** (`on-writing_vault_documents.md`) para gerar resumos a partir de grupos de `(:Claim)` e `(:Sentence)` nodes (`on-writing_vault_documents.md`, Retrieval Notes).
- Desenvolvimento de lógica para incluir links de volta para os blocos Tier 1 originais, utilizando a sintaxe `^blk_id` (Obsidian block anchors) e `clarifai:id` (conforme `idea-creating_tier1_documents.md`).
- Implementação da **escrita atômica para arquivos Markdown** (`docs/project/epic_1/sprint_plan.md` e `on-filehandle_conflicts.md`):
    1. Escreve o conteúdo completo em um arquivo temporário (`.tmp`).
    2. Executa `fsync()` no arquivo temporário para garantir que os dados sejam gravados no disco.
    3. Renomeia atomicamente o arquivo temporário para o nome do arquivo final (substituindo o original).
- Configuração de integração com o pipeline existente (recebendo grupos de claims/sentenças processados).
- Documentação do processo de geração e formato dos resumos Tier 2 (`on-writing_vault_documents.md`).
- Implementação de logging detalhado e rastreabilidade para o processo de geração de resumos.

### Excluído
- Vinculação de conceitos dentro dos resumos (será adicionada no Sprint 4).
- Interface de usuário para visualização ou edição de resumos.
- Otimizações avançadas de desempenho para volumes muito grandes de dados (foco na funcionalidade principal).
- Geração de resumos Tier 3 (conceitos ou sujeitos).
- Processamento em lote de grandes volumes de dados (foco na funcionalidade por grupo de claims/sentenças).

## Critérios de Aceitação
- O agente de geração de resumos produz resumos coerentes e informativos a partir de `(:Claim)` nodes agrupados do Tier 1.
- Os resumos incluem links de volta para os blocos Tier 1 originais (`^blk_id`) que são funcionais no Obsidian e permitem a navegação direta.
- O sistema implementa e utiliza a escrita atômica para arquivos Markdown de forma robusta e segura.
- A integração do agente funciona corretamente com o pipeline existente, recebendo os dados necessários para a geração de resumos.
- A documentação descreve claramente o processo de geração, a estrutura do output Markdown Tier 2 e o formato dos links (`on-writing_vault_documents.md`).
- Testes automatizados demonstram a funcionalidade do agente, a correção dos links e a robustez da escrita atômica de arquivos.

## Dependências
- Pipeline Claimify implementado (da tarefa anterior deste sprint), fornecendo `(:Claim)` e `(:Sentence)` nodes.
- Nós `(:Claim)` e `(:Sentence)` criados no Neo4j (da tarefa anterior deste sprint).
- O `utterances` vector store (de Sprint 2), para auxiliar na recuperação de enunciados relevantes para agrupamento (`on-writing_vault_documents.md`, Retrieval Notes).
- Acesso ao sistema de arquivos para escrita de arquivos Markdown no vault.
- Definição clara do formato de resumos Tier 2 (`on-writing_vault_documents.md`).

## Entregáveis
- Código-fonte do agente de geração de resumos Tier 2.
- Implementação da lógica de escrita atômica para arquivos Markdown.
- Documentação técnica do processo e formato dos resumos.
- Testes unitários e de integração para o agente e a escrita de arquivos.
- Exemplos de arquivos de resumo Tier 2 gerados, com links para os blocos originais.

## Estimativa de Esforço
- 4 dias de trabalho

## Riscos e Mitigações
- **Risco**: Qualidade inconsistente dos resumos gerados (e.g., resumos superficiais, imprecisos).
  - **Mitigação**: Iteração e ajuste dos prompts do agente de resumo; implementação de métricas de qualidade básicas para resumos (e.g., coerência, concisão) e feedback para ajuste de prompts.
- **Risco**: Perda de dados ou corrupção de arquivos durante a escrita no vault.
  - **Mitigação**: A utilização estrita da técnica de escrita atômica (`.tmp` -> `fsync` -> `rename`) é a principal mitigação para este risco. Incluir verificações de integridade pós-escrita.
- **Risco**: Links quebrados para blocos Tier 1 ou incorreção na anotação dos links.
  - **Mitigação**: Implementar validação rigorosa dos IDs de blocos e da sintaxe dos links Markdown antes da escrita; incluir testes de integração que simulem a navegação no Obsidian para verificar a funcionalidade dos links.

## Notas Técnicas
- Utilizar a técnica de escrita atômica (`write-temp` → `fsync` → `rename`) para garantir a integridade dos arquivos no vault, prevenindo condições de corrida e corrupção.
- O agente deve agrupar `(:Claim)` nodes que são semanticamente relacionados e derivar um resumo coerente.
- Assegurar que os links para os blocos Tier 1 (`^blk_id`) sejam gerados de forma determinística e correspondam aos IDs existentes nos arquivos Tier 1.
- Estruturar o código de forma modular, permitindo a futura adição da vinculação de conceitos de forma limpa.
- O formato do resumo Tier 2 deve ser claro, conciso e seguir o padrão especificado em `on-writing_vault_documents.md` (formato de lista com links inline).
- Considerar o uso de parâmetros configuráveis para o agente de resumo (e.g., tamanho máximo do resumo, modelo LLM a ser utilizado), preparando para Sprint 6.
