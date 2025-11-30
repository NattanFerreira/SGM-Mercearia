# SGM-Mercearia 🏪

Sistema de Gerenciamento de Mercearia — aplicação web para controle de clientes, dívidas, pagamentos e relatórios financeiros.

---

## 📋 Sobre o Projeto

O **SGM-Mercearia** é um sistema desenvolvido para facilitar o gerenciamento de uma mercearia, permitindo:

- **Cadastro de clientes** (nome, CPF, endereço, telefone e email)
- **Lançamento de dívidas** com controle de valor, data de lançamento e prazo de vencimento
- **Registro de pagamentos** parciais ou totais sobre as dívidas
- **Renegociação automática** de dívidas acumuladas quando um novo lançamento é feito (atualiza prazos pendentes)
- **Controle de usuários** com dois níveis de acesso:
  - **Caixista**: adiciona clientes, lança dívidas, registra pagamentos e consulta histórico
  - **Administrador**: todas as permissões do caixista + cadastro/remoção de usuários e acesso ao dashboard de relatórios
- **Interface web interativa** com busca dinâmica de clientes e visualização de histórico em tempo real

### Tecnologias Utilizadas

- **Backend**: Python 3.x + Flask
- **Banco de Dados**: SQLite (via Flask-SQLAlchemy)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla JS)
- **Autenticação**: Sessões Flask com hashing de senha (Werkzeug)

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

- **Python 3.8+** instalado
- **pip** (gerenciador de pacotes do Python)

### Passo 1: Clonar o repositório

```powershell
git clone https://github.com/Pedrollucas/SGM-Mercearia.git
cd SGM-Mercearia
```

### Passo 2: Criar e ativar o ambiente virtual

No **PowerShell** (Windows):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

No **Linux/macOS** (Bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Passo 3: Instalar as dependências

```powershell
pip install -r requirements.txt
```

### Passo 4: Executar a aplicação

```powershell
python app.py
```

A aplicação estará disponível em: **http://127.0.0.1:5000**

---

## 🔐 Login Inicial

Na primeira execução, o sistema cria automaticamente um usuário administrador:

- **Usuário**: `adm`
- **Senha**: `adm`

> ⚠️ **Importante**: Altere essa senha após o primeiro acesso para garantir a segurança do sistema.

---

## 📂 Estrutura do Projeto

```
SGM-Mercearia/
│
├── app.py                  # Aplicação Flask (inicializa o servidor e cria o DB)
├── requirements.txt        # Dependências do projeto
├── sgm.db                  # Banco de dados SQLite (criado automaticamente)
│
├── web/
│   ├── __init__.py
│   ├── models.py           # Modelos SQLAlchemy (Usuario, Cliente, Divida, Pagamento, Renegociacao)
│   └── routes.py           # Rotas e lógica de negócio (CRUD, autenticação, APIs)
│
├── templates/              # Templates HTML (Jinja2)
│   ├── base.html           # Layout base (header, aside, main)
│   ├── login.html          # Tela de login
│   ├── home.html           # Página inicial (pós-login)
│   ├── clientes_*.html     # CRUD de clientes
│   ├── dividas_*.html      # CRUD de dívidas
│   ├── pagar_form.html     # Formulário de pagamento
│   ├── usuarios_*.html     # CRUD de usuários (apenas admin)
│   └── relatorios_*.html   # Dashboard e extratos
│
├── modelos/                # Modelos originais do CLI (referência)
├── controles/              # Controles originais do CLI (referência)
└── utils/                  # Utilitários (referência)
```

---

## 🧑‍💼 Funcionalidades por Perfil

### Caixista

- Adicionar, listar e visualizar clientes
- Lançar novas dívidas
- Registrar pagamentos (parciais ou totais)
- Consultar histórico de dívidas e pagamentos de cada cliente

### Administrador

- Todas as funcionalidades do Caixista
- Cadastrar e remover usuários
- Acessar dashboard com relatórios financeiros (total de dívidas, recebimentos, etc.)
- Renegociar dívidas (atualizar prazo e juros)

---

## 📦 Dependências Principais

- **Flask** (3.1.2+): framework web
- **Flask-SQLAlchemy** (3.1.1+): ORM para SQLite
- **Werkzeug** (3.1.3+): utilitários (hashing de senha, segurança)

Veja o arquivo `requirements.txt` para a lista completa.

---

## 🛠️ Melhorias Futuras (Roadmap)

- [ ] Proteção CSRF com Flask-WTF
- [ ] Hashing de senha com bcrypt (mais seguro)
- [ ] Validação avançada de formulários
- [ ] Edição/exclusão de clientes e dívidas
- [ ] Exportação de relatórios em PDF
- [ ] Testes automatizados (pytest)
- [ ] Deploy em servidor de produção (Gunicorn + Nginx)

---

## 👨‍💻 Autores

Desenvolvido por: 
**Bruna Nunes** ([brun4nune5s](https://github.com/brun4nune5s)),
**Nattan Ferreira Lopes** ([NattanFerreira](https://github.com/NattanFerreira)),
**Pedro Henrique** ([pehandrade](https://github.com/pehandrade)) e
**Pedro Lucas** ([Pedrollucas](https://github.com/Pedrollucas))

Para dúvidas ou sugestões, abra uma issue no repositório ou entre em contato.