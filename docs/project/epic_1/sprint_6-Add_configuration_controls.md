# Tarefa: Adicionar Controles de Configuração para Jobs Agendados

## Descrição
Implementar controles de configuração granulares para jobs agendados no ClarifAI, permitindo que os usuários configurem o comportamento de cada job individualmente. Isso incluirá a capacidade de habilitar/desabilitar jobs, configurar a execução apenas manual e gerenciar suas programações (cron) através de um arquivo de configuração e toggles na interface de usuário (UI).

## Escopo

### Incluído
- Implementação de controles de configuração para jobs agendados, conforme especificado em `docs/arch/design_config_panel.md` (Seção 5: "Override scheduler behavior per job") e `docs/arch/design_review_panel.md` (Seção 3: "Job Log Preview").
- Suporte para os seguintes estados e parâmetros por job:
    - `enabled: true/false`: Habilita ou desabilita a execução automática do job.
    - `manual_only: true/false`: Indica se o job só pode ser acionado manualmente (quando `enabled` for `true`).
    - `cron: "0 3 * * *"`: Configura a programação cron para jobs automáticos (conforme `docs/arch/design_config_panel.md`).
- Implementação de toggles e campos de entrada na UI (Gradio) para gerenciar essas configurações por job, conforme `docs/arch/design_config_panel.md`.
- Configuração para diversos tipos de jobs agendados, incluindo (mas não limitado a):
    - Higiene de conceito (e.g., `concept_embedding_refresh`).
    - Sincronização do vault (e.g., `vault_sync`).
    - Agentes de resumo (e.g., `concept_summary_refresh`, `subject_summary_refresh`).
- Persistência das configurações de jobs no arquivo `clarifai.config.yaml` (sob a seção `scheduler:`), seguindo a estrutura de `docs/arch/design_config_panel.md`.
- Implementação da lógica no `clarifai-scheduler` para **ler e respeitar** essas configurações por job (`enabled`, `manual_only`, `cron`).
- Documentação clara de todas as opções de configuração de jobs e seus efeitos.
- Implementação de logging para alterações de estado de configuração de jobs e suas execuções.

### Excluído
- Implementação de agendamento avançado que não seja baseado em cron strings simples (e.g., "executar a cada 5 minutos e 30 segundos").
- Interface de usuário para visualização *detalhada* de histórico de execução de jobs (e.g., gráficos de tempo de execução, uso de recursos), além do status básico e "próxima execução" (conforme `docs/arch/design_review_panel.md`).
- Otimizações avançadas de desempenho que não são inerentes à leitura/aplicação das configurações.
- Configuração de infraestrutura de agendamento (e.g., configuração do `APScheduler` em si).
- Sistema de notificação para falhas de jobs além do logging interno.

## Critérios de Aceitação
- Controles de configuração para jobs agendados estão implementados e funcionais na UI e no `clarifai.config.yaml`.
- Os estados `enabled`, `manual_only` e os parâmetros `cron` são suportados e funcionam corretamente para todos os jobs configuráveis.
- A configuração funciona para os tipos de jobs especificados (higiene de conceito, sincronização, agentes de resumo).
- As configurações de jobs são persistidas corretamente no `clarifai.config.yaml`.
- O `clarifai-scheduler` lê e respeita as configurações (`enabled`, `manual_only`, `cron`) para cada job antes de executá-lo.
- A interface de usuário para ativar/desativar jobs e ajustar suas configurações é intuitiva e funcional.
- Documentação clara de todas as opções e seus efeitos está disponível.
- O logging de alterações de estado de configuração de jobs e suas execuções é implementado.

## Dependências
- Sistema de agendamento de jobs (`clarifai-scheduler` com `APScheduler`) implementado (de Sprint 3).
- Sistema de persistência de configurações (`clarifai.config.yaml` e sua UI/módulo de gerenciamento, de tarefa anterior deste sprint).
- Definição clara de todos os jobs configuráveis (especialmente em `docs/arch/design_config_panel.md`).

## Entregáveis
- Código-fonte dos controles de configuração de jobs (dentro do módulo de configuração e no `clarifai-scheduler`).
- Atualização da UI (Gradio) para incluir os controles por job.
- Implementação da lógica de persistência das configurações de jobs no `clarifai.config.yaml`.
- Documentação de todas as opções configuráveis de jobs e seus efeitos.
- Testes de funcionalidade abrangentes para os controles de configuração de jobs.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Desativação acidental de jobs críticos ou configuração de `cron` inválida.
  - **Mitigação**: Implementar confirmações na UI para alterações importantes e validação rigorosa para `cron` strings. O logging detalhado de alterações de configuração ajudará na auditoria.
- **Risco**: Inconsistência entre a configuração e o estado real dos jobs no `scheduler`.
  - **Mitigação**: Garantir que o `clarifai-scheduler` *sempre* releia as configurações (ou seja notificado sobre mudanças) antes de decidir executar um job. O arquivo `clarifai.config.yaml` deve ser a fonte da verdade.
- **Risco**: Confusão do usuário sobre os diferentes estados dos jobs (`enabled`, `manual_only`, `pausa global`).
  - **Mitigação**: Fornecer feedback claro na UI (e.g., status "Pausado (Global)", "Habilitado", "Apenas Manual"). A documentação deve explicar claramente a hierarquia dos controles.

## Notas Técnicas
- O modelo de dados para as configurações de jobs no `clarifai.config.yaml` deve seguir a estrutura de `docs/arch/design_config_panel.md` (Seção 5, `scheduler:`).
- A UI deve permitir que o usuário veja e edite o `cron` string diretamente, e não apenas toggles simples, para maior flexibilidade.
- O `clarifai-scheduler` precisará de uma lógica que, para cada job, verifique primeiro a *pausa global* (da tarefa anterior deste sprint) e, em seguida, as configurações específicas do job (`enabled`, `manual_only`).
- A implementação deve ser modular, permitindo a fácil adição de novos jobs configuráveis no futuro.
- Assegurar que as alterações de configuração de jobs sejam registradas no log, incluindo quem fez a alteração (se aplicável, para ambientes multi-usuário) e o valor anterior/novo.
