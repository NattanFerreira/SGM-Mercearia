import sys
from pathlib import Path
from datetime import date, timedelta

from flask import Flask
from werkzeug.security import generate_password_hash

# Garantir que o diretório raiz do projeto esteja no sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.models import db, Usuario, Cliente, Divida, Pagamento, Renegociacao


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sgm.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'seed-only'
    db.init_app(app)
    return app


def ensure_admin():
    if not Usuario.query.filter_by(nome='adm').first():
        adm = Usuario(
            nome='adm', cpf=None, email='adm', senha_hash=generate_password_hash('adm'), tipo='Administrador'
        )
        db.session.add(adm)
        db.session.commit()


def ensure_caixista():
    if not Usuario.query.filter_by(nome='caixa').first():
        u = Usuario(
            nome='caixa', cpf=None, email='caixa@local', senha_hash=generate_password_hash('caixa'), tipo='Caixista'
        )
        db.session.add(u)
        db.session.commit()


def seed_clientes_dividas():
    if Cliente.query.count() > 0:
        print('[seed] Clientes já existem; pulando inserção de clientes/dívidas.')
        return

    # Lista maior de clientes (Cliente: nome, cpf, endereco, celular - sem email)
    clientes_data = [
        ('Maria Souza','123.456.789-00','Rua das Flores, 123','(11) 99999-1111'),
        ('João Santos','987.654.321-00','Av. Central, 456','(11) 98888-2222'),
        ('Ana Lima','111.222.333-44','Rua Azul, 789','(11) 97777-3333'),
        ('Carlos Pereira','222.333.444-55','Rua Verde, 10','(11) 96666-4444'),
        ('Beatriz Alves','333.444.555-66','Av. Paulista, 1000','(11) 95555-1234'),
        ('Rafael Gomes','444.555.666-77','Rua do Sol, 55','(11) 94444-8888'),
        ('Luciana Prado','555.666.777-88','Rua das Acácias, 12','(11) 93333-7777'),
        ('Fernanda Dias','666.777.888-99','Av. Brasil, 222','(11) 92222-6666'),
        ('Marcos Silva','777.888.999-00','Rua Santa, 345','(11) 91111-5555'),
        ('Patrícia Souza','888.999.000-11','Rua Azul, 99','(11) 90000-4444'),
        ('Daniel Costa','999.000.111-22','Av. Norte, 321','(11) 98888-3333'),
        ('Priscila Rocha','000.111.222-33','Rua Limoeiro, 8','(11) 97777-2222'),
        ('Thiago Nunes','111.222.333-45','Rua das Orquídeas, 70','(11) 96666-1111'),
        ('Aline Souza','222.333.444-56','Av. Mar, 400','(11) 95555-0000'),
        ('Bruno Araújo','333.444.555-67','Rua Horizonte, 23','(11) 94444-9999'),
    ]

    clientes = [
        Cliente(nome=n, cpf=cpf, endereco=end, celular=cel)
        for (n, cpf, end, cel) in clientes_data
    ]
    db.session.add_all(clientes)
    db.session.flush()

    # Dívidas por cliente (2 por cliente): usar saldo_devedor, data_vencimento
    dividas = []
    for c in clientes:
        val1 = round(150+ c.id*7.5,2)
        val2 = round(60 + c.id*3.2,2)
        dividas.append(Divida(cliente_id=c.id, descricao='Compra do mês', valor_original=val1, saldo_devedor=val1, data_vencimento=date.today()+timedelta(days=10 + (c.id%5)*5), status='Pendente'))
        dividas.append(Divida(cliente_id=c.id, descricao='Itens avulsos', valor_original=val2, saldo_devedor=val2, data_vencimento=date.today()+timedelta(days=25 + (c.id%3)*7), status='Pendente'))
    db.session.add_all(dividas)
    db.session.flush()

    # Pagamentos parciais (em algumas dívidas): usar data_pagamento, meio_pagamento
    pagamentos = []
    for i, d in enumerate(dividas):
        if i % 3 == 0:  # a cada três dívidas, registrar um pagamento
            val = round(d.valor_original * 0.4, 2)
            pagamentos.append(Pagamento(divida_id=d.id, valor=val, data_pagamento=date.today(), meio_pagamento='Pix' if i%2==0 else 'Dinheiro'))
            d.saldo_devedor = round(d.saldo_devedor - val, 2)
    db.session.add_all(pagamentos)

    # Renegociações (algumas dívidas): usar data_reneg, nova_data_venc, juros_percent
    reneg = []
    for i, d in enumerate(dividas):
        if i % 5 == 0:
            reneg.append(Renegociacao(divida_id=d.id, data_reneg=date.today(), nova_data_venc=date.today()+timedelta(days=45), juros_percent=0))
    db.session.add_all(reneg)

    db.session.commit()
    print(f"[seed] Inseridos {len(clientes)} clientes, {len(dividas)} dívidas, {len(pagamentos)} pagamentos e {len(reneg)} renegociações.")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        ensure_admin()
        ensure_caixista()
        seed_clientes_dividas()
        print('[seed] Concluído.')
