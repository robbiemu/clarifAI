# Tarefa: Projetar UI do Painel de Configuração para Subject Summary & Concept Summary Agents

## Descrição
Desenvolver a interface de usuário (UI) do painel de configuração para os agentes Subject Summary e Concept Summary, utilizando Gradio. A UI permitirá que os usuários configurem e personalizem a geração de páginas de assunto e conceito, e deverá ler e persistir todas as configurações no arquivo `settings/aclarai.config.yaml`, conforme as especificações em `docs/arch/design_config_panel.md`.

## Escopo

### Incluído
- Implementação da UI do painel de configuração em **Gradio**, expandindo a seção "Highlight & Summary" (criada em Sprint 9) para incluir controles para os agentes de resumo de conceito e de assunto.
- Implementação de controles para o **Subject Summary Agent**, conforme definido em `docs/arch/design_config_panel.md` (Seção 4):
    - Sliders ou inputs para `similarity_threshold`, `min_concepts`, e `max_concepts`.
    - Switches de toggle para `allow_web_search` e `skip_if_incoherent`.
    - Campo dropdown ou de texto para `model.subject_summary`.
- Implementação de controles para o **Concept Summary Agent**, conforme definido em `docs/arch/design_config_panel.md` (Seção 4):
    - Input numérico para `max_examples`.
    - Switches de toggle para `skip_if_no_claims` e `include_see_also`.
- **Sincronização com `settings/aclarai.config.yaml`:** Garantir que a UI sempre leia o estado atual do arquivo de configuração e que qualquer alteração seja persistida imediatamente no arquivo, conforme o comportamento especificado em `docs/arch/design_config_panel.md` (Seção "UI Behavior Notes").
- Implementação de validação de entrada (e.g., para valores numéricos) com feedback visual ao usuário, rejeitando configurações inválidas, conforme `design_config_panel.md`.
- Documentação clara da interface e da correspondência de cada controle com os parâmetros no arquivo `aclarai.config.yaml`.

### Excluído
- Implementação backend dos agentes de resumo (eles apenas consomem a configuração gerada por esta UI).
- Visualização de resultados de geração ou logs de execução dos agentes.
- Otimizações avançadas de desempenho da UI além do que o Gradio oferece nativamente.
- Integração com sistemas externos ou análise estatística avançada de resultados.

## Critérios de Aceitação
- A UI do painel de configuração para os agentes de resumo de conceito e de assunto está implementada em Gradio com um layout intuitivo.
- Todos os controles (`sliders`, `inputs`, `toggles`) para `subject_summaries` e `concept_summaries` estão funcionais e corretamente mapeados para os parâmetros em `aclarai.config.yaml`.
- A UI **carrega e reflete corretamente** o estado atual das configurações do `aclarai.config.yaml` ao ser exibida.
- Todas as alterações feitas na UI são **salvas corretamente** de volta no arquivo `aclarai.config.yaml` de forma atômica.
- A validação de entrada funciona, prevenindo a gravação de valores inválidos (e.g., texto em um campo numérico) e fornecendo feedback ao usuário.
- A documentação descreve claramente cada componente da UI e o parâmetro de configuração correspondente que ele controla.
- A interface é responsiva e acessível dentro dos padrões do Gradio.

## Dependências
- Sistema de configuração base implementado, que lê/escreve o arquivo `aclarai.config.yaml` (`docs/project/epic_1/sprint_6-Implement_aclarais_core_config.md`).
- Estrutura de UI em Gradio estabelecida (`docs/project/epic_1/sprint_1-Scaffold_aclarai_frontend.md`).
- Definição clara dos parâmetros configuráveis no documento de arquitetura principal: `docs/arch/design_config_panel.md`.
- Definição dos agentes que esta UI irá configurar: `docs/arch/on-writing_vault_documents.md`.

## Entregáveis
- Código-fonte da UI do painel de configuração (dentro do serviço `services/aclarai-ui`).
- Integração completa com o sistema de configuração para ler/escrever no `aclarai.config.yaml`.
- Documentação da interface e seus componentes.
- Testes de funcionalidade e usabilidade.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Interface complexa demais para usuários não técnicos.
  - **Mitigação**: Focar em design intuitivo e incluir dicas de ajuda (`tooltips`) que expliquem o propósito de cada parâmetro.
- **Risco**: Configurações incorretas levando a resultados inesperados na geração de documentos.
  - **Mitigação**: Implementar validação em tempo real e fornecer valores padrão sensatos para todos os parâmetros, conforme definido em `design_config_panel.md`.
- **Risco**: Inconsistência entre a UI e o arquivo YAML se o arquivo for editado manualmente enquanto a UI está aberta.
  - **Mitigação**: A UI deve ser a fonte de verdade para as alterações enquanto estiver ativa, ou deve ter um botão de "Recarregar Configurações". A documentação deve alertar sobre edições externas concorrentes.

## Notas Técnicas
- Utilizar componentes de UI consistentes com o restante da aplicação Gradio.
- A persistência das configurações no arquivo `aclarai.config.yaml` é o objetivo principal; a UI é a interface para essa operação.
- Estruturar o layout da UI com `gr.Blocks` e seções recolhíveis (`gr.Accordion`) para manter a organização, espelhando a estrutura do `design_config_panel.md`.
- O logging deve registrar quando as configurações são alteradas através da UI para fins de auditoria.
