# Tarefa: Agendar Subject Jobs

## Descrição
Implementar o agendamento dos jobs de clusterização de conceitos (`subject_group_refresh`) e de geração de resumos de assunto (`subject_summary_agent`) no sistema de agendamento do aclarai. Isso garantirá a execução periódica e configurável desses processos, a sobrescrita segura dos arquivos gerados e o respeito ao toggle de pausa global do sistema.

## Escopo

### Incluído
- Adição dos jobs `subject_group_refresh` (para clusterização de conceitos) e `subject_summary_agent` (para geração de páginas `[[Subject:XYZ]]`) ao agendador (`aclarai-scheduler`).
- Configuração de periodicidade e horários de execução para ambos os jobs, utilizando o `aclarai-scheduler` (de `docs/project/epic_1/sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`) e respeitando as configurações de `cron` e `enabled/manual_only` definidas em `docs/arch/design_config_panel.md` (Seção 5: "Automation & Scheduler Control") e gerenciadas pela tarefa de Sprint 6 "Adicionar Controles de Configuração para Jobs Agendados".
- Implementação de suporte ao **toggle de pausa global** (`.aclarai_pause` ou UI switch) para ambos os jobs, garantindo que eles não sejam executados quando a automação estiver pausada, conforme `docs/project/epic_1/sprint_6-Pause_automation.md`.
- Garantia de que a saída do `subject_summary_agent` (os arquivos Markdown `[[Subject:XYZ]]` gerados) utilize a **escrita atômica** (`.tmp` → `fsync` → `rename`), conforme implementado em `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md` e detalhado em `docs/arch/on-filehandle_conflicts.md`.
- Configuração para garantir que a saída dos jobs de assunto suporte a **sincronização de vault**, o que implica que os arquivos Markdown gerados conterão os marcadores `aclarai:id` e `ver=` (conforme `docs/arch/on-graph_vault_synchronization.md`) para que o `vault-watcher` (de Sprint 4) e o `block_syncing_loop` (de Sprint 4) possam detectar e processar as alterações.
- Documentação clara do processo de agendamento e configuração desses jobs.
- Implementação de testes para verificar o correto agendamento e execução dos jobs sob diferentes configurações e estados de pausa.

### Excluído
- Implementação dos jobs `subject_group_refresh` (clusterização) e `subject_summary_agent` (geração de páginas) em si (já coberto por tarefas anteriores ou paralelas deste sprint).
- Interface de usuário para configuração de agendamento (já coberto pela tarefa "Projetar UI do Painel de Configuração para Subject Summary & Concept Summary Agents" deste sprint e a tarefa de Sprint 6 "Adicionar Controles de Configuração para Jobs Agendados").
- Otimizações avançadas de desempenho que não são inerentes ao agendamento.
- Processamento em lote de grandes volumes de dados (o foco é na execução periódica dos jobs).
- Sistema de notificação avançado para falhas (além do logging).

## Critérios de Aceitação
- Jobs `subject_group_refresh` e `subject_summary_agent` são adicionados e registrados corretamente no agendador.
- A periodicidade e os horários de execução são configurados adequadamente para ambos os jobs, respeitando as definições do `aclarai.config.yaml` (de `design_config_panel.md`).
- O sistema de agendamento respeita o toggle de pausa global, impedindo a execução dos jobs quando a automação está pausada.
- O sistema garante que a saída do `subject_summary_agent` utiliza a escrita atômica para evitar arquivos corrompidos.
- O suporte à sincronização de vault é configurado e funcional, com os arquivos de saída do `subject_summary_agent` contendo os metadados necessários (`aclarai:id`, `ver=`).
- O logging detalhado é implementado para rastreabilidade de execução dos jobs.
- A documentação clara do processo de agendamento e configuração está disponível.
- Testes demonstram a funcionalidade e robustez do agendamento, incluindo cenários de execução programada, de acordo com as configurações, e respeitando o estado de pausa.

## Dependências
- Sistema de agendamento (`aclarai-scheduler` com `APScheduler`) implementado e funcional (`docs/project/epic_1/sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`).
- Job de clusterização de conceitos (`subject_group_refresh`) implementado (`docs/project/epic_1/sprint_10-Implement_Concept_clustering_job.md`).
- Job de geração de resumos de assunto (`subject_summary_agent`) implementado (`docs/project/epic_1/sprint_10-Implement_Subject_Summary_Agent.md`).
- Sistema de escrita atômica implementado (`docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md`).
- Sistema de sincronização de vault (`vault-watcher` e `block_syncing_loop` de Sprint 4) implementado e funcional.
- Sistema de configuração de jobs (`docs/project/epic_1/sprint_6-Add_configuration_controls.md`) e de pausa global (`docs/project/epic_1/sprint_6-Pause_automation.md`) implementados.

## Entregáveis
- Código-fonte da configuração de agendamento para os jobs de assunto (dentro do serviço `aclarai-scheduler`).
- Implementação da integração com o agendador para esses jobs.
- Configuração que garante a escrita atômica e a compatibilidade com a sincronização de vault para a saída do `subject_summary_agent`.
- Documentação do processo e configuração.
- Testes unitários e de integração.

## Estimativa de Esforço
- 1 dia de trabalho

## Riscos e Mitigações
- **Risco**: Conflitos de agendamento com outros jobs ou sobrecarga do sistema.
  - **Mitigação**: Configurar horários de execução em períodos de baixa utilização. As opções de `cron` em `design_config_panel.md` permitem flexibilidade. O `aclarai-scheduler` deve ter mecanismos de escalonamento básico.
- **Risco**: Falhas durante a execução dos jobs causando inconsistências nos arquivos ou no grafo.
  - **Mitigação**: A escrita atômica é a principal mitigação para a integridade dos arquivos. O logging detalhado e a capacidade de reprocessamento do vault sync (`docs/arch/on-graph_vault_synchronization.md`) atuam como fallback.
- **Risco**: Consumo excessivo de recursos durante a execução dos jobs.
  - **Mitigação**: Monitorar o uso de recursos dos contêineres. Ajustar a frequência de execução dos jobs (e.g., semanal em vez de diária) via configuração se o impacto for alto.

## Notas Técnicas
- Utilizar `APScheduler` para o agendamento robusto, conforme já estabelecido.
- A configuração dos jobs deve ser lida do `aclarai.config.yaml` e aplicada pelo `aclarai-scheduler`, permitindo controle granular (`enabled`, `manual_only`, `cron`).
- É crucial que o job de geração de Markdown (`subject_summary_agent`) inclua os metadados `aclarai:id` e `ver=` em seus arquivos de saída para serem detectados e sincronizados corretamente pelo sistema de vault sync.
- O logging deve ser claro sobre o status de agendamento, início, fim e resultado de cada execução de job.
- Este agendamento contribui para a proposta de valor de "Subject Pages" em `docs/project/product_definition.md`.
