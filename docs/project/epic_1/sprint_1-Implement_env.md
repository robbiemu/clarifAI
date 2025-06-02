# Tarefa: Implementar injeção de .env e fallback para host.docker.internal para DBs externos

## Descrição
Implementar um sistema de injeção de variáveis de ambiente a partir de arquivos .env e configurar fallback para host.docker.internal, permitindo a conexão com bancos de dados externos ao ambiente Docker.

## Escopo

### Incluído
- Criação de um sistema de carregamento de variáveis de ambiente a partir de arquivos .env
- Implementação de lógica de fallback para host.docker.internal quando necessário
- Configuração de conexões para bancos de dados externos (Neo4j e Postgres)
- Documentação do uso de variáveis de ambiente e conexões externas
- Implementação de validação de variáveis obrigatórias
- Criação de arquivo .env.example com configurações padrão e documentação

### Excluído
- Implementação de sistema de secrets para produção
- Configuração de autenticação avançada para bancos de dados
- Implementação de balanceamento de carga para múltiplas instâncias de DB
- Configuração de SSL/TLS para conexões de banco de dados
- Migração de dados entre ambientes

## Critérios de Aceitação
- Sistema carrega corretamente variáveis de ambiente a partir de arquivos .env
- Conexões com bancos de dados externos funcionam quando configuradas via variáveis de ambiente
- Fallback para host.docker.internal é aplicado automaticamente quando apropriado
- Validação de variáveis obrigatórias com mensagens de erro claras
- Documentação clara sobre como configurar conexões externas
- Arquivo .env.example com todas as variáveis necessárias e comentários explicativos

## Dependências
- Docker Compose stack configurado
- Definição das variáveis de ambiente necessárias para cada serviço
- Acesso a bancos de dados externos para testes

## Entregáveis
- Sistema de carregamento de variáveis de ambiente implementado
- Lógica de fallback para host.docker.internal
- Arquivo .env.example com documentação
- Documentação de uso e configuração
- Testes de conexão com bancos de dados externos

## Estimativa de Esforço
- 1 dia de trabalho

## Riscos e Mitigações
- **Risco**: Falha na conexão com bancos de dados externos
  - **Mitigação**: Implementar retry com backoff e logs detalhados de erro
- **Risco**: Vazamento de credenciais sensíveis
  - **Mitigação**: Garantir que arquivos .env não sejam versionados e documentar boas práticas
- **Risco**: Incompatibilidade entre diferentes sistemas operacionais
  - [de-prioritized] good for future, but not for this epic
  - **Mitigação**: Testar em múltiplos ambientes (Linux, macOS, Windows). 

## Notas Técnicas
- Utilizar bibliotecas padrão para carregamento de .env (dotenv em Node.js, python-dotenv em Python)
- Implementar validação de variáveis obrigatórias no início da execução
- Considerar o uso de valores padrão sensatos para variáveis não críticas
- Documentar claramente o formato esperado para URLs de conexão
- Implementar logging detalhado para facilitar diagnóstico de problemas de conexão
- Considerar diferentes comportamentos de host.docker.internal em diferentes versões do Docker
