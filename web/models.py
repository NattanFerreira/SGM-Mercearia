from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False, default='Caixa')
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Usuario {self.nome}>"

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(20), nullable=True)
    celular = db.Column(db.String(50), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)
    nivel_confianca = db.Column(db.String(50), default='Novo')
    limite_credito = db.Column(db.Float, default=200.0)
    notificacoes_ativas = db.Column(db.Boolean, default=True)

    dividas = db.relationship('Divida', backref='cliente', lazy=True)

    def __repr__(self):
        return f"<Cliente {self.nome}>"

class Divida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    valor_original = db.Column(db.Float, nullable=False)
    data_venda = db.Column(db.Date, default=date.today)
    data_vencimento = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.String(255), default='')
    status = db.Column(db.String(50), default='Pendente')
    saldo_devedor = db.Column(db.Float, nullable=False)

    pagamentos = db.relationship('Pagamento', backref='divida', lazy=True)
    renegociacoes = db.relationship('Renegociacao', backref='divida', lazy=True)

    def aplicar_pagamento(self, pagamento):
        # aplicar pagamento persistente
        self.saldo_devedor -= pagamento.valor
        if self.saldo_devedor <= 0:
            self.saldo_devedor = 0.0
            self.status = 'Paga'

    def registrar_pagamento(self, pagamento):
        db.session.add(pagamento)
        self.aplicar_pagamento(pagamento)

    def renegociar(self, nova_data, juros_percent, usuario_responsavel):
        acrescimo = self.saldo_devedor * (juros_percent / 100)
        self.saldo_devedor += acrescimo
        self.data_vencimento = nova_data
        self.status = 'Renegociada'
        reneg = Renegociacao(divida_id=self.id, nova_data_venc=nova_data, juros_percent=juros_percent, usuario_responsavel=usuario_responsavel)
        db.session.add(reneg)

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    divida_id = db.Column(db.Integer, db.ForeignKey('divida.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_pagamento = db.Column(db.Date, default=date.today)
    meio_pagamento = db.Column(db.String(50), nullable=True)
    usuario_responsavel = db.Column(db.String(150), nullable=True)

class Renegociacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    divida_id = db.Column(db.Integer, db.ForeignKey('divida.id'), nullable=False)
    nova_data_venc = db.Column(db.Date, nullable=False)
    juros_percent = db.Column(db.Float, nullable=False)
    data_reneg = db.Column(db.Date, default=date.today)
    usuario_responsavel = db.Column(db.String(150), nullable=True)
