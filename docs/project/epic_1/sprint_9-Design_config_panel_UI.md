# Tarefa: Projetar UI do Painel de Configuração para Jobs de Destaque de Conceito

## Descrição
Desenvolver a interface de usuário do painel de configuração para jobs de destaque de conceito, permitindo aos usuários configurar e personalizar a geração de páginas de destaque como Top Concepts e Trending Topics, conforme a estrutura e os parâmetros definidos em `docs/arch/design_config_panel.md` (Seção 4: "Concept Highlight & Summary Jobs").

## Escopo

### Incluído
- Design e implementação da UI do painel de configuração para jobs de destaque de conceito utilizando **Gradio**.
- Adição de inputs para `top_concepts` e `trending_topics` sob uma nova seção "Highlight & Summary", conforme `design_config_panel.md`.
- Implementação de campos para configuração de:
    - `metric` (métrica de classificação)
    - `count` (quantidade de conceitos)
    - `percent` (percentual de crescimento mínimo)
    - `window_days` (janela de tempo para análise)
    - `target_file` (arquivo de destino)
    (Todos estes parâmetros são definidos em `design_config_panel.md`).
- Inclusão de inputs de toggle para `min_mentions`.
- Adição de campo de preview para nomes de arquivo de saída.
- Exibição do modelo de agente selecionado (`model.trending_concepts_agent`) como somente leitura ou dropdown, conforme `design_config_panel.md` (Seção 1: "Inference Models").
- **Garantia de que a UI reflita o estado atual do `./settings/clarifai.config.yaml` e que qualquer alteração na UI seja persistida imediatamente no arquivo**, conforme o comportamento estabelecido em `docs/project/epic_1/sprint_6-Implment_ClarifAIs_core_config.md` e `design_config_panel.md` (Seção "UI Behavior Notes").
- Documentação clara da interface e seus componentes.

### Excluído
- Implementação backend dos jobs (será feita em tarefa separada).
- Visualização avançada de resultados de jobs.
- Otimizações avançadas de desempenho.
- Integração com sistemas externos.
- Análise estatística avançada de resultados.

## Critérios de Aceitação
- UI do painel de configuração implementada com layout intuitivo em Gradio.
- Inputs para `top_concepts` e `trending_topics` funcionais sob a seção "Highlight & Summary".
- Campos para todas as configurações necessárias (`metric`, `count`, `percent`, `window_days`, `target_file`) implementados e funcionais.
- Inputs de toggle para `min_mentions` funcionais.
- Campo de preview para nomes de arquivo de saída implementado.
- Exibição do modelo de agente selecionado (`model.trending_concepts_agent`) funcional.
- **A UI carrega corretamente as configurações do `./settings/clarifai.config.yaml` e salva as alterações de volta no arquivo.**
- **Validação de configurações funciona corretamente, rejeitando entradas inválidas e fornecendo feedback ao usuário**, conforme `design_config_panel.md` (Seção "UI Behavior Notes").
- Documentação clara da interface e seus componentes está disponível.
- Interface responsiva e acessível.

## Dependências
- Sistema de configuração base implementado (`docs/project/epic_1/sprint_6-Implment_ClarifAIs_core_config.md`).
- Definição clara dos parâmetros configuráveis em `docs/arch/design_config_panel.md`.
- Framework de UI Gradio escolhido e configurado (`docs/project/epic_1/sprint_1-Scaffold_ClarifAI_frontend.md`).

## Entregáveis
- Código-fonte da UI do painel de configuração (dentro do serviço `clarifai-ui`).
- Implementação de todos os campos e controles na UI.
- Documentação da interface e seus componentes.
- Testes de usabilidade e funcionalidade.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Interface complexa demais para usuários não técnicos.
  - **Mitigação**: Focar em design intuitivo e incluir dicas contextuais (`tooltips`). Organizar opções em categorias lógicas, conforme `design_config_panel.md`.
- **Risco**: Configurações incorretas levando a resultados inesperados.
  - **Mitigação**: Implementar validação em tempo real e fornecer valores padrão sensatos (conforme `design_config_panel.md`).
- **Risco**: Problemas de compatibilidade entre diferentes dispositivos.
  - **Mitigação**: Implementar design responsivo e testar em múltiplas plataformas.

## Notas Técnicas
- Utilizar componentes de UI consistentes com o restante da aplicação Gradio.
- A validação de entrada deve fornecer feedback imediato ao usuário, conforme `design_config_panel.md`.
- A persistência de configurações deve ser feita de forma robusta para preservar preferências do usuário.
- O layout deve ser estruturado em grupos lógicos para facilitar a compreensão, espelhando as seções de `design_config_panel.md`.
- O campo para `model.trending_concepts_agent` deve ser um dropdown populado com os modelos LLM disponíveis, ou um campo de texto se a lista for dinâmica.
