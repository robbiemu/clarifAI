# Tarefa: Configurar Monorepo e Serviços Iniciais do Projeto

## Descrição
Criar e configurar a estrutura de monorepo inicial para o projeto aclarai, estabelecendo a base para o desenvolvimento colaborativo de todos os serviços componentes.

## Escopo

### Incluído
- Criação de um único repositório GitHub para o projeto aclarai.
- Configuração da estrutura de monorepo, incluindo diretórios para cada serviço:
  - `services/aclarai-core/` (serviço principal)
  - `services/vault-watcher/` (observador de arquivos)
  - `services/scheduler/` (agendador de tarefas)
  - `services/aclarai-ui/` (interface de usuário Gradio)
  - `shared/` (para módulos Python compartilhados, como modelos de dados e utilitários)
- Configuração de um ambiente Python unificado (e.g., com Poetry Workspaces ou `pyproject.toml` para `src` layout) para gerenciar as dependências de todos os serviços.
- Adição de arquivos essenciais na raiz do monorepo e em cada serviço: README.md, .gitignore, LICENSE.
- Documentação básica da arquitetura e propósito de cada serviço no README principal.

### Excluído
- [...] (rest of the document as is)

## Critérios de Aceitação
- Um único repositório GitHub criado com a estrutura de monorepo.
- Cada subdiretório de serviço contém sua estrutura básica de diretórios apropriada.
- Arquivos README.md com descrição clara do propósito e arquitetura do serviço.
- Arquivos .gitignore adequados para as tecnologias utilizadas, configurados na raiz e/ou por serviço.
- Documentação inicial sobre como contribuir e configurar o ambiente de desenvolvimento monorepo.
- Configuração inicial do ambiente Python para todos os serviços.

## Notas Técnicas
- **Priorizar a implementação de um repositório monolítico (monorepo) dado que todos os serviços serão desenvolvidos em Python (incluindo o frontend Gradio), o que simplificará o gerenciamento de dependências, compartilhamento de código e tooling.**
- Utilizar templates de diretório/estrutura para manter consistência entre os serviços.
- Configurar hooks de git (e.g., via pre-commit) para garantir qualidade de código desde o início.
- Documentar convenções de nomenclatura e estrutura para facilitar a navegação e o desenvolvimento dentro do monorepo.
