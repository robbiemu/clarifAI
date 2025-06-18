# Tarefa: Implementar plugin padrão para sistema de conversão de formato plugável

## Descrição
Desenvolver um plugin padrão para o sistema de conversão de formato plugável do aclarai, permitindo a importação e conversão de formatos de arquivo não reconhecidos por plugins específicos, garantindo que o sistema possa processar uma ampla variedade de formatos de entrada.

## Escopo

### Incluído
- Implementação de um plugin de fallback que sempre aceita a entrada
- Desenvolvimento de um agente baseado em LLM para interpretar e formatar conteúdo não estruturado
- Criação de lógica para detectar e extrair conversas de texto não estruturado
- Implementação de formatação para saída em Markdown padrão do aclarai
- Adição de metadados apropriados (título, participantes, contagem de mensagens)
- **Assegurar que o plugin se conforme integralmente à interface `Plugin` (métodos `can_accept` e `convert`) e que seja configurado para ser descoberto e utilizado pelo orquestrador central de conversão.**
- Documentação de uso e extensão do plugin

### Excluído
- Implementação de plugins específicos para formatos conhecidos (JSON, CSV, etc.)
- Otimização avançada para redução de uso de tokens LLM
- Interface de usuário para configuração do plugin
- Suporte para formatos binários ou criptografados

## Critérios de Aceitação
- O plugin sempre retorna `True` de `can_accept(...)`
- O agente LLM é capaz de extrair conversas de texto não estruturado
- O plugin formata corretamente a saída como Markdown com estrutura `speaker: text`
- Metadados apropriados são incluídos: título, participantes, contagem de mensagens
- **O plugin adere à interface `Plugin` e pode ser carregado/utilizado com sucesso pela função central de conversão de arquivos (`convert_file_to_markdowns`).**
- O plugin lida graciosamente com falhas, retornando `None` quando não consegue extrair conversas
- Documentação clara sobre como usar e estender o plugin

## Dependências
- Sistema de plugins base implementado
- Acesso a modelos LLM para processamento de texto
- Definição da estrutura de saída Markdown padrão do aclarai

## Entregáveis
- Código-fonte do plugin de fallback
- Implementação do agente LLM para extração de conversas
- Testes unitários e de integração
- Documentação de uso e extensão
- Exemplos de conversão para diferentes tipos de entrada

## Estimativa de Esforço
- 3 dias de trabalho

## Riscos e Mitigações
- **Risco**: Qualidade inconsistente na extração de conversas de texto não estruturado
  - **Mitigação**: Implementar verificações de qualidade internas para a saída do LLM (e.g., padrões esperados de `speaker: text`, contagem mínima de mensagens) e garantir logging detalhado para o monitoramento da qualidade da extração.
- **Risco**: Uso excessivo de tokens LLM
  - **Mitigação**: Implementar estratégias de chunking e limites de tamanho
- **Risco**: Falhas silenciosas na extração
  - **Mitigação**: Assegurar logging detalhado para todas as etapas de extração e conversão do LLM, permitindo o diagnóstico preciso de falhas internas.

## Notas Técnicas
- Utilizar prompts cuidadosamente projetados para guiar o LLM na extração de conversas
- Implementar estratégias de chunking para lidar com arquivos maiores
- Considerar o uso de heurísticas simples antes de recorrer ao LLM para casos óbvios
- Armazenar metadados sobre o uso do plugin de fallback para análise futura
- Implementar cache para evitar reprocessamento de conteúdos similares
