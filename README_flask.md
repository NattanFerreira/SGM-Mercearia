# SGM-Mercearia - Web (Flask + SQLite)

Este README descreve como executar a versão básica em Flask com persistência SQLite criada a partir do app CLI.

Instalação:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Rodar:

```powershell
python app.py
# Acesse http://127.0.0.1:5000
```

Observações:

- O banco SQLite `sgm.db` será criado automaticamente na primeira execução.
- Use as telas: Clientes, Dívidas, Usuários e Dashboard.
