# Tarefa: Construir Painel de Importação Gradio

## Descrição
Desenvolver um Painel de Importação completo utilizando Gradio, fornecendo uma interface de usuário intuitiva para que os usuários possam fazer upload e processar arquivos de conversação. Este painel integrará o orquestrador de plugins de importação (da tarefa anterior), selecionará automaticamente o plugin apropriado e exibirá o status da importação, fornecendo feedback em tempo real e um resumo pós-importação, conforme o design em `docs/arch/design_import_panel.md`.

## Escopo

### Incluído
- Implementação de um **Painel Gradio** que inclua:
    - Um **seletor de arquivo (`gr.File`)** para upload de arquivos de conversação, conforme o requisito do plano de sprint "File picker for uploading raw conversation files". Os formatos aceitos incluem `.json`, `.md`, `.txt`, `.csv`, `.zip`, conforme `docs/arch/design_import_panel.md` (Seção 1).
    - Uma **área de log (`gr.Textbox`)** ou componente similar para exibir a "Live Import Queue" (fila de importação ao vivo) com o status de cada arquivo (`✅ Imported`, `❌ Failed`, `⚠️ Fallback`), fornecendo o feedback em tempo real mencionado em `docs/arch/design_import_panel.md` (Seção 3).
- Desenvolvimento da lógica de frontend para **seleção automática do plugin apropriado** para o arquivo carregado, chamando o método `can_accept()` do orquestrador de plugins (da tarefa anterior de Sprint 8), conforme o requisito do plano de sprint "Selects appropriate format plugin automatically via can_accept()".
- Integração robusta com o **orquestrador de plugins de importação** (da tarefa anterior de Sprint 8) para processar o arquivo e emitir o Markdown Tier 1, conforme o requisito do plano de sprint "Invokes plugin orchestrator to emit Tier 1 Markdown".
- Exibição clara e em tempo real do **status de importação** para cada arquivo (sucesso, ignorado - ex: duplicata, erro - ex: falha de conversão), utilizando os componentes de UI apropriados do Gradio, conforme o requisito do plano de sprint "Displays import status (success, skipped, error)".
- Suporte visual explícito para o **plugin de fallback** quando nenhum plugin específico aceita o arquivo, indicando que o fallback foi utilizado, conforme o requisito do plano de sprint "Supports fallback plugin if no plugin accepts the file" e `docs/arch/design_import_panel.md` (Seção 3).
- Implementação de uma **"Post-import Summary"** (resumo pós-importação) que aparece após todos os arquivos serem processados, exibindo contagens de arquivos importados, ignorados e falhos, e links para os arquivos importados (conforme `docs/arch/design_import_panel.md`, Seção 4).
- Documentação clara do uso e extensão do painel de importação, incluindo como ele interage com o orquestrador e os plugins.

### Excluído
- Implementação de novos plugins de formato específicos (estes são desenvolvidos separadamente).
- Visualização avançada do conteúdo importado ou edição de conteúdo diretamente na interface do painel de importação.
- Otimizações avançadas de desempenho para uploads de arquivos *extremamente* grandes que exigem streaming complexo no frontend.
- Processamento em lote de múltiplos arquivos através de um único `gr.File` (o foco é no processamento de arquivos individuais e na exibição de seu status).

## Critérios de Aceitação
- O Painel Gradio está implementado com um seletor de arquivo funcional para upload de conversações.
- O sistema seleciona automaticamente o plugin apropriado via `can_accept()` e invoca o orquestrador de plugins.
- A integração com o orquestrador de plugins funciona corretamente, resultando na emissão de Markdown Tier 1.
- O status de importação (sucesso, ignorado, erro) é exibido claramente e em tempo real na "Live Import Queue".
- O uso do plugin de fallback é indicado visualmente quando necessário.
- A "Post-import Summary" é exibida corretamente após a conclusão de todas as importações.
- A documentação clara do uso e extensão do painel está disponível.
- Testes automatizados demonstram a funcionalidade com diferentes tipos de arquivo e cenários de importação (sucesso, falha, duplicata, fallback).

## Dependências
- Gerenciador de plugins e orquestrador de importação implementados (da tarefa anterior de Sprint 8).
- Gradio instalado e configurado (de Sprint 1).
- Pelo menos um plugin de importação funcional (ex: o plugin de fallback de Sprint 2).
- Plugin de fallback implementado e funcional (de Sprint 2, conforme `docs/arch/idea-default_plugin_task.md`).

## Entregáveis
- Código-fonte do Painel de Importação Gradio (dentro de `services/aclarai-ui`).
- Implementação da "Live Import Queue" e da "Post-import Summary" na UI.
- Lógica de integração com o orquestrador de plugins.
- Documentação do uso e extensão do painel.
- Testes de funcionalidade para o painel de importação.

## Estimativa de Esforço
- 2 dias de trabalho

## Riscos e Mitigações
- **Risco**: Problemas de compatibilidade ou desempenho com uploads de arquivos grandes no Gradio.
  - **Mitigação**: Testar com arquivos de tamanhos variados. O Gradio lida bem com uploads, mas para arquivos *extremamente* grandes, pode ser necessário otimizar a forma como o orquestrador processa internamente (o que está fora do escopo desta tarefa).
- **Risco**: Experiência de usuário confusa devido a feedback insuficiente ou layout desorganizado.
  - **Mitigação**: Focar no design intuitivo e no feedback claro em cada etapa, seguindo rigorosamente o layout e os componentes definidos em `docs/arch/design_import_panel.md`.
- **Risco**: Falhas durante o processo de importação não são comunicadas claramente ao usuário.
  - **Mitigação**: Implementar tratamento robusto de erros no frontend, exibindo mensagens claras e úteis para o usuário em caso de falha de um plugin ou do orquestrador.

## Notas Técnicas
- Utilizar os recursos do Gradio para criar uma interface limpa e responsiva, focando na usabilidade.
- A "Live Import Queue" deve ser um `gr.Textbox` ou similar que é atualizado dinamicamente via `gr.update()` ou retornos de geradores Gradio.
- A integração com o orquestrador de plugins será feita chamando a função Python do orquestrador diretamente do backend do Gradio.
- O Gradio já lida com o upload de arquivos para o backend; o foco aqui é na lógica de como o backend do Gradio interage com o orquestrador e como o status é reportado de volta para a UI.
- O feedback visual deve ser contínuo, não apenas um status final.
