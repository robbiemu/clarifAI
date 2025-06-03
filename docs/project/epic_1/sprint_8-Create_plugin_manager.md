# Tarefa: Criar Gerenciador de Plugins e Orquestrador de Importação

## Descrição
Desenvolver um gerenciador de plugins e orquestrador de importação centralizado que coordene o processo de ingestão de arquivos de conversação. Este componente será responsável por escanear e selecionar automaticamente o plugin de formato apropriado (incluindo um plugin de fallback), passar o arquivo para o plugin selecionado e registrar o status da importação, conforme o fluxo definido em `docs/arch/on-pluggable_formats.md`.

## Escopo

### Incluído
- Implementação de um **gerenciador de plugins** que escaneia e descobre todos os plugins de formato conhecidos (implementações da interface `Plugin` de `docs/arch/on-pluggable_formats.md`).
- Desenvolvimento da **lógica de orquestração (`convert_file_to_markdowns` de `docs/arch/on-pluggable_formats.md`)** para:
    - Iterar sobre os plugins descobertos.
    - Executar o método `can_accept(raw_input)` de cada plugin para determinar qual plugin pode processar o arquivo.
    - Executar o método `convert(raw_input, input_path)` do *primeiro* plugin onde `can_accept()` retorna `true`.
- Implementação de passagem do arquivo de entrada (`raw_input` e `input_path`) para o plugin selecionado.
- Registro detalhado do **status de importação** para cada arquivo processado (sucesso, ignorado - ex: duplicata, erro - ex: falha de conversão), que será utilizado pela UI de importação (próxima tarefa de Sprint 8).
- Suporte para o **plugin de fallback** (implementado em Sprint 2, conforme `docs/arch/idea-default_plugin_task.md`) quando nenhum plugin específico de formato aceita o arquivo. O orquestrador deve garantir que o fallback seja a última opção.
- Integração robusta com o sistema de plugins existente, garantindo que a interface `Plugin` (`can_accept`, `convert`) seja respeitada.
- Documentação clara do processo de orquestração, da descoberta de plugins e de como estender o sistema com novos plugins.
- Implementação de tratamento de erros e exceções durante o processo de seleção e conversão de plugins.

### Excluído
- Interface de usuário para visualização *interativa* do processo de importação (será implementada na tarefa seguinte deste sprint, "Build Gradio Import Panel").
- Implementação de plugins específicos para novos formatos (estes são desenvolvidos separadamente e plugados no sistema).
- Otimizações avançadas de desempenho para orquestração de *milhões* de arquivos.
- Processamento em lote de grandes volumes de arquivos (o foco é na orquestração de um arquivo por vez, que pode ser chamado em um loop).
- Análise avançada de conteúdo de arquivos para além do que os plugins `can_accept()` fornecem.

## Critérios de Aceitação
- O gerenciador escaneia e descobre corretamente todos os plugins de formato disponíveis.
- O sistema executa o método `can_accept()` dos plugins na ordem correta e seleciona o primeiro plugin que retorna `true`.
- O arquivo de entrada é passado corretamente para o método `convert()` do plugin selecionado.
- O status de importação (sucesso, ignorado, erro) é registrado adequadamente para cada arquivo processado.
- O plugin de fallback é utilizado corretamente quando nenhum plugin específico aceita o arquivo.
- A integração funciona robustamente com a interface `Plugin` existente (`docs/arch/on-pluggable_formats.md`).
- A documentação clara do processo de orquestração e de como estender o sistema com novos plugins está disponível.
- Testes automatizados demonstram a funcionalidade com diferentes tipos de arquivo (aceitos por plugins específicos, aceitos pelo fallback, e não aceitos por nenhum).

## Dependências
- Sistema de plugins base e interface `Plugin` implementados (conforme `docs/arch/on-pluggable_formats.md`).
- Pelo menos um plugin de fallback implementado e funcional (de Sprint 2, conforme `docs/arch/idea-default_plugin_task.md`).
- Sistema de criação de arquivos Markdown Tier 1 (de Sprint 2), que será o consumidor final da saída do orquestrador.

## Entregáveis
- Código-fonte do gerenciador de plugins e orquestrador de importação.
- Implementação da lógica de registro de status de importação.
- Documentação do processo de orquestração e extensão.
- Testes unitários e de integração para o orquestrador.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Falhas na detecção do plugin apropriado ou na ordem de prioridade dos plugins.
  - **Mitigação**: Implementar logging detalhado do processo de seleção de plugins. Definir e documentar uma ordem de prioridade clara para plugins (ex: plugins mais específicos primeiro, fallback por último).
- **Risco**: Conflitos ou erros entre plugins com capacidades sobrepostas.
  - **Mitigação**: A regra de "primeiro plugin que aceita" mitiga isso. No entanto, testar com cenários de sobreposição e garantir que os plugins sejam bem isolados.
- **Risco**: Falhas durante o processo de importação dentro de um plugin não são adequadamente tratadas pelo orquestrador.
  - **Mitigação**: O orquestrador deve capturar exceções lançadas pelos plugins (`try...except` ao chamar `plugin.convert()`) e registrar o status de erro, impedindo que uma falha em um plugin interrompa o processo geral de importação.

## Notas Técnicas
- Considerar o uso de um padrão de design Chain of Responsibility ou Strategy para a cascata de plugins, embora a implementação direta de um loop `for` sobre uma lista ordenada de plugins seja suficiente para o MVP.
- Implementar um mecanismo de descoberta dinâmica de plugins (e.g., usando `entry_points` ou um registro simples) para que novos plugins possam ser adicionados sem modificar o código do orquestrador.
- Estruturar logs de forma clara para facilitar o diagnóstico de problemas, indicando qual plugin foi tentado, qual aceitou, e o resultado da conversão.
- A saída do orator (`list[MarkdownOutput]`) deve ser passada para o componente responsável por escrever os arquivos Markdown Tier 1 no vault (de Sprint 2).
