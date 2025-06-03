# Tarefa: Implementar UI e Arquivo de Configuração para Funções de Modelo, Limiares e Janelas

## Descrição
Desenvolver **tanto uma interface de usuário (UI) quanto um arquivo de configuração persistente (`clarifai.config.yaml`)** para gerenciar as funções de modelo, limiares de similaridade e janelas de contexto do ClarifAI. A UI deverá sempre refletir o estado atual do arquivo YAML e qualquer alteração na UI deverá ser persistida imediatamente no arquivo, conforme `docs/arch/design_config_panel.md`. Este sistema expandirá o escopo de configuração para incluir todos os aspectos configuráveis do ClarifAI.

## Escopo

### Incluído
- Desenvolvimento de **uma UI (em Gradio)** e de um **arquivo de configuração (`clarifai.config.yaml`)** para gerenciar as funções de modelo, limiares e janelas, conforme a estrutura e seções propostas em `docs/arch/design_config_panel.md`.
- Implementação da lógica para que a UI **leia e reflita o estado atual** do `clarifai.config.yaml`.
- Implementação da lógica para que as alterações feitas na UI sejam **gravadas de volta no `clarifai.config.yaml`**, garantindo a persistência das configurações.
- Expansão do escopo de configuração para incluir:
  - Todas as funções de modelo Claimify (incluindo escolhas de modelo de Embedding), conforme `docs/arch/design_config_panel.md` (Seção 1: "Model & Embedding Settings" e `docs/arch/on-evaluation_agents.md`, Seção "Model Configuration").
  - Limiares de Claim/concept, conforme `docs/arch/design_config_panel.md` (Seção 2: "Thresholds & Parameters" e `docs/arch/on-evaluation_agents.md`, Seção "Thresholds").
  - Parâmetros de Window (p, f), conforme `docs/arch/design_config_panel.md` (Seção 2: "Thresholds & Parameters" e `docs/arch/on-graph_vault_synchronization.md`, Seção "Context Window for Claimify Processing").
- Implementação de validação de configurações, rejeitando entradas inválidas (e.g., valores não numéricos para limiares) e fornecendo feedback ao usuário (conforme `docs/arch/design_config_panel.md`, "UI Behavior Notes").
- Persistência de configurações de forma robusta.
- Documentação clara de todas as opções configuráveis e seus efeitos.
- Implementação de valores padrão sensatos para todas as configurações, conforme `docs/arch/design_config_panel.md` (ex: valores para `threshold.concept_merge`, `window.claimify.p/f`).

### Excluído
- Implementação de configuração dinâmica em tempo real que permita hot-reloading de modelos ou agentes sem reiniciar os serviços do ClarifAI. A aplicação de novas configurações persistidas poderá exigir um reinício controlado.
- Interface de usuário avançada com visualizações complexas ou otimizações de desempenho focadas em renderização gráfica fora das capacidades padrão do Gradio.
- Otimizações avançadas de desempenho para o *processamento* das configurações em si.
- Configuração da infraestrutura subjacente (ex: Docker Compose, redes, provedores de LLM externos).
- Migração automática de configurações legadas de formatos anteriores (foco no `clarifai.config.yaml` canônico).

## Critérios de Aceitação
- **A UI e o arquivo de configuração (`clarifai.config.yaml`) estão implementados e funcionais.**
- A UI **carrega e reflete** corretamente o estado atual do `clarifai.config.yaml`.
- As alterações feitas na UI são **salvas corretamente** no `clarifai.config.yaml`.
- Todas as funções de modelo Claimify (incluindo escolhas de modelo de Embedding) são configuráveis através da UI e persistidas no arquivo.
- Limiares de Claim/concept podem ser ajustados através da UI e persistidos no arquivo.
- Parâmetros de Window (p, f) são configuráveis através da UI e persistidos no arquivo.
- Validação de configurações funciona corretamente, impedindo a persistência de valores inválidos e informando o usuário.
- Documentação clara de todas as opções e seus efeitos está disponível no repositório.
- Valores padrão sensatos estão implementados para todas as opções configuráveis.

## Dependências
- Definição clara de todos os parâmetros configuráveis, especialmente em `docs/arch/design_config_panel.md`.
- Serviço `clarifai-ui` (Gradio) scaffolded (de Sprint 1).
- Módulos dos serviços ClarifAI capazes de ler as configurações do arquivo `clarifai.config.yaml`.

## Entregáveis
- Código-fonte da UI (Gradio) para o painel de configuração.
- Módulo para gerenciamento de leitura/escrita do `clarifai.config.yaml`.
- Arquivo `clarifai.config.yaml` de exemplo com configurações padrão.
- Documentação de todas as opções configuráveis e seus valores padrão.
- Testes de funcionalidade para validação, persistência e a correta sincronização entre UI e arquivo.

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Configurações inválidas causando falhas no sistema.
  - **Mitigação**: Implementar validação robusta das entradas na UI e antes da persistência no arquivo YAML, além de fornecer valores padrão seguros, conforme `docs/arch/design_config_panel.md`.
- **Risco**: Inconsistências entre o estado da UI e o conteúdo do `clarifai.config.yaml` devido a edições externas ou falhas de persistência.
  - **Mitigação**: Garantir que a UI sempre leia o arquivo YAML ao ser carregada/recarregada. Implementar o salvamento da UI de forma atômica e robusta. Documentar que edições manuais *enquanto a UI está aberta* podem ser sobrescritas pela UI.
- **Risco**: Complexidade excessiva na UI/arquivo para usuários.
  - **Mitigação**: Organizar opções em categorias lógicas (como as seções propostas em `docs/arch/design_config_panel.md`) e fornecer documentação clara com exemplos de uso.
- **Risco**: Perda de configurações devido a erros de escrita ou sobrescrita acidental.
  - **Mitigação**: Implementar um sistema simples de backup automático do `clarifai.config.yaml` antes de qualquer alteração significativa, e considerar o uso de escrita atômica para o arquivo de configuração, se o sistema operacional permitir.

## Notas Técnicas
- A UI deve ser construída com Gradio e deve ter uma estrutura que permita a integração futura com outros painéis de controle.
- A persistência das configurações deve ser feita em um arquivo **YAML** (`clarifai.config.yaml`).
- A lógica de sincronização entre a UI e o arquivo YAML é crítica: a UI deve carregar o estado do arquivo ao iniciar e cada alteração na UI deve ser imediatamente escrita de volta ao arquivo (ou em uma ação explícita de "Salvar" na UI), conforme `docs/arch/design_config_panel.md` ("UI Behavior Notes").
- As opções devem ser organizadas em categorias lógicas (`model`, `embedding`, `threshold`, `window`), espelhando a estrutura em `docs/arch/design_config_panel.md`, para facilitar a navegação e o uso.
- Implementar um sistema de logging para registrar alterações de configuração, facilitando a auditoria e a depuração.
- A configuração dos modelos deve ser flexível o suficiente para suportar diferentes provedores (e.g., `gpt-4`, `claude-3-opus`, `openrouter:gemma-2b`, `ollama:mistral`), conforme `docs/arch/design_config_panel.md`.
