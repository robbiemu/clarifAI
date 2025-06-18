# Tarefa: Exibir Pontuações de Avaliação em Metadados Markdown

## Descrição
Implementar um sistema para exibir as pontuações de avaliação de claims (`entailed_score`, `coverage_score`, `decontextualization_score`) diretamente nos metadados Markdown dos arquivos Tier 1. Isso proporcionará transparência sobre a qualidade dos claims extraídos e facilitará a filtragem e análise por usuários e outros agentes, conforme o formato especificado em `docs/arch/on-evaluation_agents.md`.

## Escopo

### Incluído
- Implementação da lógica para **anexar blocos de metadados `<!-- aclarai:... -->`** ao Markdown Tier 1 dos blocos de origem dos claims, após a conclusão da avaliação de qualidade (por todos os três agentes de avaliação).
- Desenvolvimento de um **formato padronizado para a exibição de pontuações** dentro desses blocos de metadados, conforme o exemplo em `docs/arch/on-evaluation_agents.md` (Seção "Storage").
- Inclusão de **uma linha separada para cada pontuação**: `entailment`, `coverage`, e `decontextualization`.
- Implementação de **formatação consistente** para os valores das pontuações e **tratamento adequado de valores nulos** (ex: exibindo `null` ou `N/A`), conforme `docs/arch/on-evaluation_agents.md` (Seção "Failure Modes").
- **Integração** com o sistema de avaliação existente (os agentes de `entailment`, `coverage` e `decontextualization`) para obter as pontuações finais dos claims.
- **Utilização da lógica de escrita atômica para arquivos Markdown** (implementada em Sprint 3, detalhada em `docs/arch/on-filehandle_conflicts.md`) para garantir a segurança e integridade dos arquivos durante a atualização.
- Documentação clara do formato dos metadados Markdown e da interpretação das pontuações.
- Implementação de testes para verificar a correta exibição das pontuações em diversos cenários, incluindo valores numéricos e `null`.
- Garantia de que, ao anexar blocos de metadados de pontuação no Markdown Tier 1, os marcadores aclarai:id e ver= existentes nos blocos modificados sejam preservados e que a propriedade ver= seja incrementada, para compatibilidade com o sistema de sincronização do vault (docs/arch/on-graph_vault_synchronization.md).

### Excluído
- Interface de usuário para visualização gráfica ou interativa das pontuações (o foco é na exibição textual no Markdown).
- Análise estatística avançada de pontuações dentro deste componente.
- Otimizações avançadas de desempenho que não são inerentes à operação de escrita de metadados.
- Processamento em lote de grandes volumes de dados que excedam a capacidade de atualização incremental de arquivos.

## Critérios de Aceitação
- Blocos `<!-- aclarai:... -->` são anexados corretamente ao Markdown Tier 1 dos blocos de origem dos claims.
- O formato padronizado para exibição de pontuações é utilizado de forma consistente.
- Uma linha separada é incluída para cada pontuação: `entailment`, `coverage`, e `decontextualization`.
- A formatação é consistente e os valores nulos são tratados adequadamente (ex: exibidos como `null`).
- A integração funciona corretamente com o sistema de avaliação existente para recuperar as pontuações.
- A lógica de escrita atômica é utilizada para as atualizações dos arquivos Markdown.
- A documentação clara do formato e interpretação dos metadados Markdown está disponível.
- Testes automatizados demonstram a funcionalidade e robustez da exibição das pontuações.
- Blocos <!-- aclarai:... --> são anexados corretamente ao Markdown Tier 1, e os marcadores aclarai:id e ver= dos blocos modificados são preservados e o ver= incrementado.

## Dependências
- Agentes de avaliação de `entailment`, `coverage`, e `decontextualization` implementados (tarefas anteriores deste Sprint 7), que populam as pontuações nos `(:Claim)` nodes e arestas.
- Acesso ao sistema de arquivos para atualização de arquivos Markdown Tier 1.
- Definição clara do formato de metadados `<!-- aclarai:... -->` (conforme `docs/arch/on-evaluation_agents.md`).
- Lógica de escrita atômica para arquivos Markdown implementada (de Sprint 3).

## Entregáveis
- Código-fonte do sistema de exibição de pontuações em metadados Markdown.
- Implementação da lógica de formatação padronizada e tratamento de `null` values.
- Integração com o pipeline de avaliação de claims.
- Documentação do formato e interpretação dos metadados.
- Testes unitários e de integração.

## Estimativa de Esforço
- 1 dia de trabalho

## Riscos e Mitigações
- **Risco**: Inconsistência na formatação dos metadados entre diferentes componentes ou ao longo do tempo.
  - **Mitigação**: Centralizar a lógica de formatação em um único módulo e garantir que todos os componentes que escrevem metadados a utilizem. A documentação deve ser a fonte da verdade para o formato.
- **Risco**: Problemas de compatibilidade com ferramentas de Markdown ou parsers de terceiros devido ao formato dos comentários HTML.
  - **Mitigação**: Testar a renderização dos arquivos Markdown em Obsidian e outros parsers comuns. O formato de comentário HTML (`<!-- -->`) é geralmente bem suportado e ignorado.
- **Risco**: Metadados excessivos ou mal posicionados prejudicando a legibilidade do arquivo Markdown para o usuário.
  - **Mitigação**: Manter o formato dos metadados conciso (uma linha por pontuação) e posicioná-los estrategicamente (ex: logo abaixo do bloco de texto ao qual se referem, conforme `docs/arch/on-evaluation_agents.md`).

## Notas Técnicas
- O formato de comentário HTML (`<!-- aclarai:key=value -->`) é o padrão para metadados inline, garantindo compatibilidade com Obsidian e outros parsers Markdown.
- As pontuações devem ser exibidas com precisão numérica adequada (ex: duas casas decimais para floats).
- A lógica de atualização deve ser capaz de *inserir* ou *atualizar* esses blocos de metadados sem afetar o conteúdo principal do Markdown ou outros metadados existentes.
- O logging deve registrar quando os metadados são adicionados ou atualizados em um bloco específico.
