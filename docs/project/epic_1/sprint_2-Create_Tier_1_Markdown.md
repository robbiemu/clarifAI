# Tarefa: Criar arquivos Markdown Tier 1 durante a importação

## Descrição
Implementar um sistema para criar arquivos Markdown Tier 1 durante o processo de importação de conversas, garantindo a padronização do formato, a detecção de duplicatas e a inclusão de metadados apropriados.

## Escopo

### Incluído
- Implementação de cálculo e verificação de **hash do conteúdo total do arquivo de entrada** para detectar e evitar importações duplicadas.
- Desenvolvimento de sistema para emitir arquivos Markdown para o vault, utilizando as saídas padronizadas dos plugins de conversão.
- Anotação de cada enunciado (bloco de conversa) com um `clarifai:id` único e um `^anchor` Obsidian correspondente, conforme o formato especificado em `idea-creating_tier1_documents.md`.
- Incorporação de metadados em nível de arquivo no topo do documento Markdown (ex: `participantes`, `timestamps`, `plugin_metadata`), conforme definido na estrutura `MarkdownOutput` de `on-pluggable_formats.md`.
- Implementação de estrutura de diretórios consistente para arquivos Tier 1, seguindo a configuração `paths.tier1` definida em `on-vault_layout_and_type_inference.md`.
- Documentação do formato e processo de importação para arquivos Tier 1.

### Excluído
- Processamento avançado de conteúdo (e.g., claim extraction, summarization), que será feito em etapas posteriores.
- Interface de usuário para importação (que será implementada separadamente em Sprint 7).
- Extração de claims e conceitos (será feito em sprints posteriores).
- Geração de resumos Tier 2 (será implementada posteriormente).
- Otimizações de desempenho para volumes *muito* grandes que exigem streaming ou paralelização complexa (foco na robustez para volumes razoáveis).

## Critérios de Aceitação
- Sistema calcula e verifica hash do conteúdo de entrada corretamente para evitar importações duplicadas, pulando arquivos que já foram importados.
- Arquivos Markdown Tier 1 são criados no diretório `paths.tier1` com o formato padronizado (i.e., `speaker: text` seguido por `clarifai:id` e `^anchor`).
- Cada enunciado é anotado com um `clarifai:id` único (e.g., `blk_xyz`) e um `^anchor` correspondente.
- Metadados de arquivo (ex: título, `created_at`, `participants`, `message_count`, `plugin_metadata`) são incorporados corretamente no topo do documento Markdown.
- Estrutura de diretórios para Tier 1 é criada automaticamente se não existir.
- Documentação clara sobre o formato e processo de importação de arquivos Tier 1.
- Testes automatizados demonstrando a funcionalidade, incluindo a detecção e o pulo de importações duplicadas.

## Dependências
- Sistema de plugins de importação implementado (incluindo o plugin padrão de Sprint 2).
- Definição do formato padrão para arquivos Markdown Tier 1 (em `idea-creating_tier1_documents.md`).
- Definição da estrutura `MarkdownOutput` (em `on-pluggable_formats.md`).
- Configuração de `paths.tier1` (em `on-vault_layout_and_type_inference.md`).
- Acesso de escrita ao vault para criação de arquivos.

## Entregáveis
- Código-fonte para a lógica de criação de arquivos Markdown Tier 1.
- Implementação do sistema de detecção de duplicatas baseado em hash.
- Documentação técnica do formato e processo de importação.
- Testes unitários e de integração para a pipeline de criação de arquivos e detecção de duplicatas.
- Exemplos de arquivos Markdown Tier 1 gerados com metadados e anotações.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Colisões de hash levando a falsos positivos na detecção de duplicatas.
  - **Mitigação**: Utilizar algoritmos de hash criptográficos robustos (e.g., SHA-256 ou SHA-512) para minimizar a probabilidade de colisões. Para uma validação ainda mais robusta, considerar uma verificação secundária de metadados se o hash coincidir.
- **Risco**: Inconsistência no formato de arquivos gerados (ex: erros na anotação de `clarifai:id`, `^anchor`).
  - **Mitigação**: Implementar validação rigorosa na saída dos arquivos Markdown e criar testes automatizados de "golden file" que comparem a saída gerada com exemplos de referência.
- **Risco**: Problemas de permissão ao escrever no vault ou concorrência de escrita.
  - **Mitigação**: Implementar tratamento de erros adequado para operações de escrita. Para segurança de arquivos, **utilizar a escrita atômica (`.tmp` -> `fsync` -> `rename`)** conforme especificado em `on-filehandle_conflicts.md` e `sprint_plan.md` (Sprint 3, atomic write logic).

## Notas Técnicas
- Utilizar algoritmos de hash robustos como SHA-256 para detecção de duplicatas do *conteúdo de entrada bruto*.
- Implementar a geração determinística de `clarifai:id` para cada enunciado/bloco para garantir consistência em re-importações ou reprocessamento.
- **Implementar a escrita atômica para todos os arquivos Markdown (escrever para `.tmp`, `fsync`, depois `rename`) para garantir a segurança e integridade do arquivo no vault, prevenindo corrupção ou leituras parciais por outros processos como o Obsidian.**
- Estruturar metadados no topo do arquivo Markdown de forma padronizada (e.g., YAML front-matter ou comentários HTML padronizados) para facilitar processamento futuro e legibilidade.
- O mapeamento dos arquivos Markdown para os diretórios do vault deve ser configurável via `paths.tier1` (e.g., `vault/conversations/`).
- Gerar nomes de arquivo canônicos e únicos para os arquivos Tier 1 (e.g., `YYYY-MM-DD_Source_Title.md`).
