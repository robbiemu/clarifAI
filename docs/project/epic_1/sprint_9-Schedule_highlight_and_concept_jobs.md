# Tarefa: Agendar Jobs de Destaque e Conceito

## Descrição
Implementar o agendamento dos jobs de destaque de conceito (`concept_highlight_refresh` e `concept_summary_refresh`) no sistema de agendamento do aclarai, garantindo execução periódica e consistente desses processos. Isso incluirá a configuração de sua periodicidade, horários de execução e a garantia de que suas saídas sejam compatíveis com o sistema de sincronização do vault.

## Escopo

### Incluído
- Adição dos jobs `concept_highlight_refresh` (que engloba a geração de `Top Concepts.md` e `Trending Topics - <date>.md` implementada nas tarefas "Implementar Job de Top Concepts" e "Implementar Job de Trending Topics" deste Sprint 9) e `concept_summary_refresh` (implementado na tarefa "Implementar Agente de Resumo de Conceito" deste Sprint 9) ao agendador.
- Configuração de periodicidade e horários de execução para esses jobs, utilizando o `aclarai-scheduler` (de `docs/project/epic_1/sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`) e respeitando as configurações de `cron` e `enabled/manual_only` definidas em `docs/arch/design_config_panel.md` (Seção 5: "Automation & Scheduler Control") e gerenciadas pela tarefa de Sprint 6 "Adicionar Controles de Configuração para Jobs Agendados".
- Implementação de garantias de que a saída desses jobs (os arquivos Markdown gerados) utilize a **escrita atômica** (`.tmp` → `fsync` → `rename`), conforme implementado em `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md` e detalhado em `docs/arch/on-filehandle_conflicts.md`).
- Configuração para garantir que a saída dos jobs de destaque e conceito suporte a **sincronização de vault**, o que implica que os arquivos Markdown gerados conterão os marcadores `aclarai:id` e `ver=` (conforme `docs/arch/on-graph_vault_synchronization.md`) para que o `vault-watcher` (de Sprint 4) e o `block_syncing_loop` (de Sprint 4) possam detectar e processar as alterações.
- Implementação de logging detalhado para o início, término, e resultado da execução de cada job, incluindo quaisquer erros ou avisos.
- Documentação clara do processo de agendamento e configuração desses jobs.
- Implementação de testes para verificar o correto agendamento e execução dos jobs.

### Excluído
- Implementação dos jobs em si (já coberto por tarefas anteriores deste sprint).
- Interface de usuário para configuração de agendamento (já coberto pela tarefa "Projetar UI do Painel de Configuração para Jobs de Destaque de Conceito" deste sprint e a tarefa de Sprint 6 "Adicionar Controles de Configuração para Jobs Agendados").
- Otimizações avançadas de desempenho que não são inerentes ao agendamento.
- Processamento em lote de grandes volumes de dados (o foco é na execução periódica dos jobs).
- Sistema de notificação avançado para falhas (além do logging).

## Critérios de Aceitação
- Jobs `concept_highlight_refresh` e `concept_summary_refresh` são adicionados e registrados corretamente no agendador.
- A periodicidade e os horários de execução são configurados adequadamente, respeitando as definições do `aclarai.config.yaml` (de `design_config_panel.md`).
- O sistema garante que a saída dos jobs utiliza a escrita atômica para evitar arquivos corrompidos.
- O suporte à sincronização de vault é configurado e funcional, com os arquivos de saída contendo os metadados necessários (`aclarai:id`, `ver=`).
- O logging detalhado é implementado para rastreabilidade de execução dos jobs.
- A documentação clara do processo de agendamento e configuração está disponível.
- Testes demonstram a funcionalidade e robustez do agendamento, incluindo cenários de execução programada e de acordo com as configurações.

## Dependências
- Sistema de agendamento (`aclarai-scheduler` com `APScheduler`) implementado e funcional (de `docs/project/epic_1/sprint_3-Bootstrap_scheduler_and_vault_sync_job.md`).
- Jobs `concept_highlight_refresh` (implementado nas tarefas "Implementar Job de Top Concepts" e "Implementar Job de Trending Topics" deste Sprint 9) e `concept_summary_refresh` (implementado na tarefa "Implementar Agente de Resumo de Conceito" deste Sprint 9) implementados.
- Sistema de escrita atômica implementado (de `docs/project/epic_1/sprint_3-Create_agent_and_integration_for_Tier_2.md`).
- Sistema de sincronização de vault (`vault-watcher` e `block_syncing_loop` de Sprint 4) implementado e funcional.
- Sistema de configuração de jobs (`docs/project/epic_1/sprint_6-Add_configuration_controls.md`) implementado.

## Entregáveis
- Código-fonte da configuração de agendamento para os jobs de destaque e conceito (dentro do serviço `aclarai-scheduler`).
- Implementação da integração com o agendador para esses jobs.
- Configuração que garante a escrita atômica e a compatibilidade com a sincronização de vault para a saída desses jobs.
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
- É crucial que os jobs de geração de Markdown (Top Concepts, Trending Topics, Concept Summary) incluam os metadados `aclarai:id` e `ver=` em seus arquivos de saída para serem detectados e sincronizados corretamente pelo sistema de vault sync.
- O logging deve ser claro sobre o status de agendamento, início, fim e resultado de cada execução de job.
- Este agendamento contribui para a proposta de valor de "Top Concept Page", "Trending Topics / Concepts", e "Dedicated Concept Pages" em `docs/project/product_definition.md`.
