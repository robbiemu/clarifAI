# Tarefa: Adicionar Recurso "Pausar Automação" (via Flag de Arquivo e Switch de UI)

## Descrição
Implementar um recurso para pausar temporariamente toda a automação do ClarifAI, permitindo que os usuários interrompam processos automatizados quando necessário. Este controle será possível **tanto através de um arquivo de flag no sistema de arquivos quanto por um switch na interface de usuário (UI)**. O estado da pausa deve ser persistente e verificado por todos os jobs automatizados.

## Escopo

### Incluído
- Implementação do mecanismo central para pausar e retomar **toda a automação** do sistema, conforme especificado em `docs/arch/design_config_panel.md` (Seção 5: "Automation & Scheduler Control") e `docs/arch/design_review_panel.md` (Seção 3: "Automation Status + Controls").
- Desenvolvimento do **arquivo de flag (`.clarifai_pause`)** no diretório raiz do vault para controle do estado de pausa via sistema de arquivos (conforme `docs/arch/design_config_panel.md` e `docs/arch/design_review_panel.md`).
- Criação de um **switch/toggle na interface de usuário (UI)** (parte do `clarifai-ui` em Gradio) para controle visual do estado de pausa. Este switch deverá ler o estado do arquivo de flag e, quando alternado, deverá **atualizar o arquivo `.clarifai_pause`** (conforme `docs/arch/design_review_panel.md`, "Pause Button").
- Implementação da lógica de **verificação do estado de pausa antes da execução de *qualquer* job automatizado** no `clarifai-scheduler` e `clarifai-core`. Se a pausa estiver ativa, o job deve ser ignorado ou agendado para re-execução quando a pausa for removida.
- Garantia de **persistência do estado de pausa** entre reinicializações do sistema (já que o estado é armazenado em um arquivo).
- Documentação clara do funcionamento e uso do recurso, incluindo como verificar e alterar o estado de pausa.
- Implementação de logging detalhado para alterações de estado (pausado/resumido) e tentativas de execução de jobs durante a pausa.

### Excluído
- Pausa seletiva de jobs específicos (o controle de `enabled: true/false` por job será implementado em tarefa separada, conforme `docs/arch/design_config_panel.md`, Seção 5: "Override scheduler behavior per job").
- Agendamento de pausas automáticas (e.g., "pausar por X horas").
- Interface de usuário avançada com visualização de status detalhado de *jobs individuais* durante a pausa.
- Notificações externas (e.g., e-mail, Slack) sobre o estado de pausa.
- Integração com sistemas de monitoramento externos.

## Critérios de Aceitação
- O mecanismo para pausar e retomar toda a automação do ClarifAI funciona corretamente e desabilita a execução de jobs.
- O arquivo de flag `.clarifai_pause` é corretamente criado/removido e reconhecido pelo sistema.
- O switch na UI altera corretamente o estado de pausa (criando/removendo o arquivo `.clarifai_pause`) e reflete visualmente o estado atual.
- O sistema verifica o estado de pausa antes de executar **qualquer job automatizado** e respeita a pausa.
- O estado de pausa persiste corretamente entre reinicializações do ClarifAI.
- A documentação clara do funcionamento e uso do recurso está disponível.
- O logging de alterações de estado de pausa e tentativas de execução durante a pausa é implementado.

## Dependências
- Sistema de agendamento de jobs (`clarifai-scheduler`) implementado (de Sprint 3).
- Sistema de persistência de configurações (para `clarifai.config.yaml`, de tarefa anterior deste sprint).
- Interface de usuário Gradio básica implementada (de Sprint 1, para o switch).

## Entregáveis
- Código-fonte do mecanismo de pausa (incluindo a lógica de criação/verificação do arquivo de flag).
- Implementação do switch na UI (Gradio) e sua lógica de interação com o arquivo de flag.
- Lógica de verificação do estado de pausa nos módulos dos jobs.
- Documentação do funcionamento e uso do recurso de pausa.
- Testes de funcionalidade abrangentes, cobrindo cenários de pausa/retomada via arquivo e via UI.

## Estimativa de Esforço
- 1 dia de trabalho

## Riscos e Mitigações
- **Risco**: Pausa esquecida causando interrupção prolongada de processos críticos.
  - **Mitigação**: Implementar notificações visuais claras na UI (e.g., um banner "Automação Pausada" na `Review Panel`, conforme `docs/arch/design_review_panel.md`) e logging frequente para indicar o estado de pausa.
- **Risco**: Inconsistência entre o arquivo de flag e o estado interno da UI ou dos serviços.
  - **Mitigação**: O mecanismo de pausa deve ser o arquivo `.clarifai_pause`. A UI e todos os serviços devem *ler* esse arquivo para determinar o estado de pausa, e a UI deve *escrever* nesse arquivo para alterá-lo. Isso centraliza o controle e minimiza inconsistências.
- **Risco**: Falha na detecção do estado de pausa em componentes distribuídos ou em jobs que são executados muito rapidamente.
  - **Mitigação**: Assegurar que a verificação do arquivo de pausa seja a primeira coisa que um job faz. Implementar um cache com TTL curto para o estado do arquivo de pausa em cada serviço, se a leitura direta do arquivo for um overhead. O arquivo sendo o "estado da verdade" é crucial.

## Notas Técnicas
- Utilizar um arquivo de flag em uma localização padronizada e facilmente acessível (ex: `.clarifai_pause` no diretório raiz do vault), conforme `docs/arch/design_config_panel.md`.
- A implementação da verificação do estado de pausa deve ser eficiente para minimizar o overhead de performance, especialmente em jobs de alta frequência.
- Considerar o uso de um timestamp no nome do arquivo de flag (e.g., `.clarifai_pause_1716316800`) ou dentro do arquivo para registrar quando a pausa foi ativada, facilitando a auditoria.
- Documentar claramente o comportamento esperado durante a pausa: jobs agendados não serão executados, jobs em andamento podem ou não ser interrompidos (dependendo da granularidade de interrupção que esta tarefa não cobre), novas requisições de processamento automático serão recusadas.
- O switch da UI deve ser parte do painel de controle da automação, conforme `docs/arch/design_review_panel.md`.
