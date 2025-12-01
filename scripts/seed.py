from app import app
from web.models import db, Usuario, Cliente, Divida, Pagamento, Renegociacao
from werkzeug.security import generate_password_hash
from datetime import date, timedelta

with app.app_context():
    # Usuários
    if not Usuario.query.filter_by(nome='adm').first():
        admin = Usuario(nome='adm', senha_hash=generate_password_hash('adm'), tipo='Administrador')
        db.session.add(admin)
    if not Usuario.query.filter_by(nome='caixa').first():
        caixa = Usuario(nome='caixa', senha_hash=generate_password_hash('caixa'), tipo='Caixa')
        db.session.add(caixa)
    db.session.commit()

    # Clientes
    clientes_data = [
        {'nome': 'Aline Souza', 'cpf': '11111111111', 'celular': '11999990001', 'endereco': 'Rua 1'},
        {'nome': 'Bruno Lima', 'cpf': '22222222222', 'celular': '11999990002', 'endereco': 'Rua 2'},
        {'nome': 'Carla Dias', 'cpf': '33333333333', 'celular': '11999990003', 'endereco': 'Rua 3'},
        {'nome': 'Daniela Alves', 'cpf': '44444444444', 'celular': '11999990004', 'endereco': 'Rua 4'},
        {'nome': 'Eduardo Silva', 'cpf': '55555555555', 'celular': '11999990005', 'endereco': 'Rua 5'},
        {'nome': 'Fernanda Costa', 'cpf': '66666666666', 'celular': '11999990006', 'endereco': 'Rua 6'},
        {'nome': 'Gustavo Rocha', 'cpf': '77777777777', 'celular': '11999990007', 'endereco': 'Rua 7'},
        {'nome': 'Helena Martins', 'cpf': '88888888888', 'celular': '11999990008', 'endereco': 'Rua 8'},
        {'nome': 'Igor Mendes', 'cpf': '99999999999', 'celular': '11999990009', 'endereco': 'Rua 9'},
        {'nome': 'Juliana Prado', 'cpf': '10101010101', 'celular': '11999990010', 'endereco': 'Rua 10'},
    ]
    clientes = {}
    for cdata in clientes_data:
        c = Cliente.query.filter_by(nome=cdata['nome']).first()
        if not c:
            c = Cliente(**cdata)
            db.session.add(c)
            db.session.commit()
        clientes[cdata['nome']] = c

    # Dívidas (vencidas, em dia, renegociadas)
    hoje = date.today()
    for idx, (nome, cliente) in enumerate(clientes.items()):
        # 1 dívida vencida
        vencida = Divida.query.filter_by(cliente_id=cliente.id, descricao='Dívida vencida').first()
        if not vencida:
            vencida = Divida(
                cliente_id=cliente.id,
                valor_original=100+idx*10,
                saldo_devedor=100+idx*10,
                data_venda=hoje - timedelta(days=40),
                data_vencimento=hoje - timedelta(days=10),
                descricao='Dívida vencida',
                status='Pendente'
            )
            db.session.add(vencida)
        # 1 dívida em dia
        em_dia = Divida.query.filter_by(cliente_id=cliente.id, descricao='Dívida em dia').first()
        if not em_dia:
            em_dia = Divida(
                cliente_id=cliente.id,
                valor_original=80+idx*8,
                saldo_devedor=80+idx*8,
                data_venda=hoje - timedelta(days=5),
                data_vencimento=hoje + timedelta(days=25),
                descricao='Dívida em dia',
                status='Pendente'
            )
            db.session.add(em_dia)
        # 1 dívida renegociada
        reneg = Divida.query.filter_by(cliente_id=cliente.id, descricao='Dívida renegociada').first()
        if not reneg:
            reneg = Divida(
                cliente_id=cliente.id,
                valor_original=120+idx*12,
                saldo_devedor=120+idx*12,
                data_venda=hoje - timedelta(days=60),
                data_vencimento=hoje + timedelta(days=15),
                descricao='Dívida renegociada',
                status='Renegociada'
            )
            db.session.add(reneg)
            db.session.commit()
            # Renegociação
            r = Renegociacao(divida_id=reneg.id, nova_data_venc=reneg.data_vencimento, juros_percent=5.0, usuario_responsavel='adm')
            db.session.add(r)
        db.session.commit()

    # Pagamentos (parciais)
    for cliente in clientes.values():
        dividas = Divida.query.filter_by(cliente_id=cliente.id).all()
        for d in dividas:
            if d.status == 'Pendente' and d.saldo_devedor > 50:
                pago = Pagamento.query.filter_by(divida_id=d.id, valor=50).first()
                if not pago:
                    p = Pagamento(divida_id=d.id, valor=50, meio_pagamento='Pix', usuario_responsavel='adm')
                    d.registrar_pagamento(p)
        db.session.commit()

    print('Seed concluído com sucesso.')
