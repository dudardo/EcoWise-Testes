# Arquitetura e Desenvolvimento do Backend - EcoWise

## Processo de Estruturação do Projeto

O desenvolvimento do backend do EcoWise foi construído sob uma abordagem iterativa, partindo de requisitos funcionais claramente definidos e evoluindo através da integração progressiva de recursos técnicos. A plataforma precisava não apenas servir conteúdo estático, mas também gerenciar autenticação de usuários, persistir dados de progresso em desafios e fornecer uma experiência contínua e sem falhas.

### Escolha das Tecnologias Fundamentais

A seleção do **Python 3.12** como linguagem de implementação ocorreu pela sua versatilidade, legibilidade e ecossistema robusto. Em contraposição a frameworks mais pesados como Django, optou-se por **Flask 2.x** — um microframework que oferece exatamente o necessário para uma aplicação web modular sem overhead desnecessário. Flask fornece decoradores intuitivos para roteamento (`@app.route()`), integração nativa com Jinja2 para templating dinâmico e gerenciamento transparente de sessões HTTP, permitindo que o desenvolvedor mantenha controle fino sobre o fluxo da aplicação.

Para persistência de dados, **SQLite** foi escolhido como banco de dados relacional embarcado. Sua natureza de arquivo único (localizado em `instance/ecowise.db`) elimina complexidades de configuração de servidores externos, enquanto ainda oferece transações ACID e suporte completo a SQL. A biblioteca **SQLAlchemy** (através de Flask-SQLAlchemy) abstrai a camada de acesso aos dados, permitindo que modelos sejam definidos como classes Python com relacionamentos tipados, facilitando manutenção e evolução futura do schema.

### Modelagem de Dados e Relacionamentos

A estrutura de dados foi pensada em torno de duas entidades principais que capturam o essencial da aplicação: `Usuario` e `DesafioConcluido`.

A tabela `Usuario` armazena informações de cadastro e autenticação: identificador único (primary key), nome, email (único), senha, telefone, data de nascimento e preferências. As senhas são hashadas utilizando **Werkzeug.security** (`generate_password_hash` com algoritmo PBKDF2), garantindo que credenciais nunca sejam armazenadas em texto plano. Adicionalmente, um campo `semana_atual` rastreia qual semana de desafios o usuário está visualizando, permitindo uma experiência personalizada.

A tabela `DesafioConcluido` implementa um relacionamento um-para-muitos com `Usuario` (chave estrangeira `user_id`). Cada registro representa a conclusão de um desafio específico em uma semana específica por um usuário específico, armazenando: id do registro, referência ao usuário, número da semana, índice do desafio dentro da semana e timestamp de conclusão. Esse modelo granular permite rastreamento preciso do progresso, geração de estatísticas futuras e auditoria de atividades.

### Camada de Autenticação e Gestão de Sessões

A autenticação foi implementada através do sistema de sessões do Flask, que utiliza cookies HTTP criptografados (`session` built-in). O fluxo é bidirecional: usuários não autenticados acessam apenas `EcoH.html` (home pública com formulários de login/cadastro), enquanto rotas protegidas verificam a presença de `session['user_id']` antes de renderizar conteúdo sensível.

As rotas `/cadastro` (POST) e `/login` (POST) recebem credenciais do frontend, executam validações (email único para cadastro, credenciais válidas para login) e, em caso de sucesso, populam a sessão. A rota `/sair` invoca `session.clear()`, eliminando instantaneamente o acesso protegido.

### API REST para Persistência de Desafios

Uma das exigências técnicas críticas era permitir que o usuário marcasse desafios como completados e que esses dados persistissem entre sessões. Para isso, foram criadas duas rotas específicas que formam uma mini-API REST:

**GET `/api/desafios/<semana>`** retorna um JSON contendo todos os desafios já completados para uma semana específica. O backend consulta a tabela `DesafioConcluido`, filtra por `user_id` (da sessão) e `semana`, e retorna uma lista de índices de desafios. Essa resposta permite que o frontend, ao carregar a página `Desafios.html`, recrie o estado visual anterior (checkboxes marcadas).

**POST `/api/desafios`** recebe um JSON com `semana` e uma lista de `desafios` (índices completados). O backend deleta todos os registros de `DesafioConcluido` para essa semana/usuário e insere os novos. Esse padrão de "delete-e-reinsert" é determinístico: qualquer que seja o estado anterior, o novo payload sempre resulta na configuração correta.

### Integração do Frontend com o Backend Assincronamente

Embora o frontend utilize HTML/CSS/JavaScript vanilla, a integração com o backend ocorre através da **Fetch API** e async/await do JavaScript moderno. O arquivo `Desafios.html` contém duas funções assíncronas críticas:

`carregarSemana()` dispara um `fetch()` para GET `/api/desafios/{semana}`, renderiza dinamicamente checkboxes para 7 desafios e marca aqueles que já foram completados segundo o banco de dados. Isso garante que ao navegar entre semanas ou recarregar a página, o estado é preservado.

`salvarEstado()` implementa um padrão de **debouncing** (delay de 600ms): cada mudança em um checkbox schedula uma requisição POST, mas se outra mudança ocorrer antes dos 600ms, o timer é resetado. Isso evita sobrecarga do servidor com múltiplas requisições durante cliques rápidos.

A **Fetch API** é preferida por não introduzir dependências externas (como jQuery ou Axios) — o projeto permanece totalmente vanilla, reduzindo tamanho e complexidade.

### Servir Recursos Estáticos e Dinâmicos

O Flask serve dois tipos de recursos estáticos: aqueles em `static/` (CSS, imagens, JavaScript) e aqueles em diretórios especiais fora de `static/` (PDFs em `Ecoartigos/`).

Para `static/`, Flask fornece automaticamente a rota `/static/<filename>` via `url_for('static', filename='...')` no Jinja2. Isso funciona seamlessly.

Para PDFs, inicialmente houve uma tentativa de servir diretamente de `/static/Ecoartigos/`, mas como esses arquivos não residem fisicamente em `static/` (estão na raiz do projeto em `/Ecoartigos/`), URLs como `{{ url_for('static', filename='Ecoartigos/art27.pdf') }}` resultavam em 404.

A solução foi criar uma rota customizada:

```python
@app.route("/pdfs/<filename>")
def download_pdf(filename):
    pdf_path = os.path.join(basedir, 'Ecoartigos')
    return send_from_directory(pdf_path, filename)
```

Aqui, `basedir` é o diretório absoluto da aplicação (calculado via `os.path.abspath(os.path.dirname(__file__))`), e `send_from_directory()` (importado de `flask`) serve o arquivo com headers HTTP apropriados, evitando exposição direta do filesystem.

### Renderização Dinâmica com Jinja2

Todos os templates (`.html` em `templates/`) são processados por **Jinja2**, o motor de templating do Flask. Isso permite embedar lógica Python diretamente no HTML:

- `{{ usuario.nome }}` — interpola o valor de uma variável Python
- `{% for desafio in desafios %}...{% endfor %}` — itera sobre coleções
- `{{ url_for('rota_name', arg=valor) }}` — gera URLs dinamicamente

O Perfil do usuário, por exemplo, é renderizado via:

```python
@app.route('/perfil')
def perfil():
    usuario = Usuario.query.get(session.get('user_id'))
    idade = calcular_idade(usuario.nascimento)
    desafios_concluidos = DesafioConcluido.query.filter_by(user_id=usuario.id).count()
    progresso_percent = (desafios_concluidos / 168) * 100  # 24 semanas x 7 desafios
    return render_template('Perfil.html', 
                          usuario=usuario, 
                          idade=idade, 
                          desafios_concluidos=desafios_concluidos,
                          progresso_percent=progresso_percent)
```

Aqui, dados calculados no backend (idade, contagem de desafios, percentual de progresso) são passados ao template como variáveis, que as utiliza para renderizar a visualização final.

### Segurança e Validação

A segurança foi implementada em camadas:

**Autenticação:** Senhas hashadas com salt, verificadas via `check_password_hash()` durante login.

**Autorização:** Rotas protegidas verificam `if 'user_id' not in session` e retornam erro ou redirecionam.

**Validação de Email:** Antes de inserir um novo usuário, consulta-se `Usuario.query.filter_by(email=email).first()` para garantir unicidade.

**Proteção de Dados:** `send_from_directory()` previne path traversal attacks (tentativas de acessar arquivos como `../../../etc/passwd`), validando nomes de arquivo.

**Sessões Criptografadas:** Flask assina cookies de sessão com `app.secret_key`, prevenindo tampering do lado do cliente.

### Ciclo de Desenvolvimento e Iteração

O desenvolvimento ocorreu em ambientes controlados — inicialmente em máquinas locais com debug ativo (`app.run(debug=True)`), depois migrado para **VS Code Codespaces** (ambiente em container Ubuntu 24.04). Isso garantiu:

- **Hot-reload:** Alterações no código `app.py` eram refletidas instantaneamente sem reiniciar.
- **Port forwarding:** O container exposava a porta 5000 para acesso via navegador.
- **Versionamento:** Git foi utilizado para rastreamento de mudanças, commits correlacionados a features.

Durante a iteração, foram identificados e corrigidos bugs:

1. **Logout não funcionava:** Todos os templates continham `{{ url_for('EcoH') }}` em vez de `{{ url_for('sair') }}` — foi necessário substituir em 10 arquivos.
2. **Desafios não persistiam:** Inicialmente, havia apenas `localStorage`, sem integração com backend — foi implementada a API REST `/api/desafios`.
3. **PDFs retornavam 404:** URLs apontavam para `static/Ecoartigos/` que não existia — foi criada a rota `/pdfs/<filename>`.

### Estrutura de Dependências

O projeto é gerenciado via pip com `requirements.txt`:

```
Flask==2.3.x
Flask-SQLAlchemy==3.0.x
Werkzeug==2.3.x
```

Essas três bibliotecas formam o núcleo. Nenhuma dependência "pesada" (como Django, async workers, caches distribuídos) foi incluída, mantendo o projeto enxuto e rápido.

### Extensibilidade e Roadmap

A arquitetura foi projetada considerando futuras expansões:

- **Adicionar mais modelos:** Novos tipos de dados podem ser incluídos em `app.py` estendendo `db.Model`.
- **Implementar relatórios:** Querys mais complexas sobre `DesafioConcluido` podem gerar dashboards de progresso.
- **API GraphQL ou REST adicional:** Rotas extras podem ser adicionadas sem reestruturação.
- **Migração para PostgreSQL:** SQLAlchemy abstrai o dialeto; uma mudança de `sqlite:///` para `postgresql://` no URI seria suficiente.

---

## Conclusão

O backend do EcoWise representa uma solução equilibrada entre simplicidade e funcionalidade. Escolhas de tecnologia (Python + Flask + SQLite) foram motivadas por pragmatismo: fornecer uma plataforma educacional confiável sem complexidade arquitetural desnecessária. A integração frontend-backend via Fetch API e micro-APIs REST, combinada com persistência estruturada em BD relacional, resulta em uma aplicação escalável dentro de seu escopo. As decisões de design — modelos simples, rotas diretas, Jinja2 para templating — facilitam manutenção futura e compreensão por novos desenvolvedores que integrem o projeto.
