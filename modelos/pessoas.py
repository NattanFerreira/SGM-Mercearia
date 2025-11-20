# ARQUIVO: pessoas.py

class Usuario:
    def __init__(self, id_usuario, nome, cpf, email, senha_hash, tipo, ativo=True):
        self.id_usuario = id_usuario
        self.nome = nome
        self.cpf = cpf
        self.email = email
        self.senha_hash = senha_hash
        self.tipo = tipo
        self.ativo = ativo
    
    def __str__(self):
        return f"Usuário: {self.nome} | Tipo: {self.tipo}"

class Cliente:
    def __init__(self, id_cliente, nome, cpf, celular, endereco, nivel_confianca="Novo", limite_credito=200.0):
        self.id_cliente = id_cliente
        self.nome = nome
        self.cpf = cpf
        self.celular = celular
        self.endereco = endereco  # Novo campo requisitado 
        
        # Campos para gestão de risco
        self.nivel_confianca = nivel_confianca  # Ex: "Bom Pagador", "Bloqueado" 
        self.limite_credito = limite_credito    # Ex: R$ 200,00 [cite: 40]
        
        self.notificacoes_ativas = True
        
    def __str__(self):
        return f"{self.nome} | Nível: {self.nivel_confianca} | Limite: R${self.limite_credito:.2f}"