from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from web.models import db, Cliente, Usuario, Divida, Pagamento, Renegociacao
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash, generate_password_hash


def register_routes(app):
    bp = Blueprint('main', __name__)

    def require_login(fn):
        def wrapper(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('main.login'))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper

    def require_admin(fn):
        def wrapper(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('main.login'))
            if session.get('user_tipo') != 'Administrador':
                flash('Acesso negado: administrador apenas.')
                return redirect(url_for('main.home'))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper

    # ---------------- Auth ----------------
    @bp.route('/', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            usuario = request.form.get('usuario')
            senha = request.form.get('senha')

            user = Usuario.query.filter((Usuario.nome == usuario) | (Usuario.email == usuario)).first()
            if user and check_password_hash(user.senha_hash, senha or ''):
                session['user_id'] = user.id
                session['user_nome'] = user.nome
                session['user_tipo'] = user.tipo
                return redirect(url_for('main.home'))
            flash('Credenciais inválidas')
        return render_template('login.html')

    @bp.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('main.login'))

    # ---------------- Home ----------------
    @bp.route('/home')
    @require_login
    def home():
        # se admin, mostra dashboard; se caixa, mostra tela inicial em branco
        tipo = session.get('user_tipo')
        if tipo == 'Administrador':
            # Dados base
            dividas = Divida.query.all()
            pagamentos = Pagamento.query.all()
            hoje = date.today()

            # KPIs
            total_a_receber = sum(d.saldo_devedor for d in dividas if d.status != 'Paga')
            total_vencido = sum(d.saldo_devedor for d in dividas if d.status != 'Paga' and d.data_vencimento < hoje)
            qtd_pagas = sum(1 for d in dividas if d.status == 'Paga')

            # Ranking top devedores (aberto)
            ranking = {}
            for d in dividas:
                if d.status == 'Paga':
                    continue
                nome = d.cliente.nome
                ranking[nome] = ranking.get(nome, 0) + d.saldo_devedor
            ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:5]
            top_labels = [n for n, _ in ranking_ordenado]
            top_values = [v for _, v in ranking_ordenado]

            # Status/atraso
            abertas = [d for d in dividas if d.status != 'Paga']
            pagas_ct = len([d for d in dividas if d.status == 'Paga'])
            vencidas_ct = len([d for d in abertas if d.data_vencimento < hoje])
            em_dia_ct = len(abertas) - vencidas_ct

            # Pagamentos por meio
            meio_map = {}
            for p in pagamentos:
                meio = p.meio_pagamento or 'Outro'
                meio_map[meio] = meio_map.get(meio, 0) + 1
            meio_labels = list(meio_map.keys())
            meio_values = list(meio_map.values())

            # Dívidas criadas por mês (últimos 6 meses)
            def ym(dt):
                return dt.year, dt.month
            from collections import defaultdict
            by_month = defaultdict(float)
            for d in dividas:
                if d.data_venda:
                    y, m = ym(d.data_venda)
                    by_month[(y, m)] += float(d.valor_original or 0)
            # montar últimos 6 meses
            labels_month = []
            values_month = []
            ref = date(hoje.year, hoje.month, 1)
            import calendar
            for i in range(5, -1, -1):
                # mês i meses atrás
                y = ref.year
                m = ref.month - i
                while m <= 0:
                    y -= 1
                    m += 12
                labels_month.append(f"{calendar.month_abbr[m]}/{str(y)[-2:]}")
                values_month.append(round(by_month.get((y, m), 0.0), 2))

            return render_template(
                'home.html',
                dashboard=True,
                total_a_receber=total_a_receber,
                total_vencido=total_vencido,
                qtd_pagas=qtd_pagas,
                ranking=ranking_ordenado,
                # dados para gráficos
                top_labels=top_labels,
                top_values=top_values,
                status_labels=['Pagas', 'Em dia', 'Vencidas'],
                status_values=[pagas_ct, em_dia_ct, vencidas_ct],
                meio_labels=meio_labels,
                meio_values=meio_values,
                month_labels=labels_month,
                month_values=values_month,
            )

        return render_template('home.html', dashboard=False)

    # ---------------- API para aside (busca) ----------------
    @bp.route('/api/clientes')
    @require_login
    def api_clientes():
        q = request.args.get('q', '').strip()
        if q:
            clientes = Cliente.query.filter(Cliente.nome.ilike(f'%{q}%')).all()
        else:
            clientes = Cliente.query.order_by(Cliente.nome).all()
        result = [{'id': c.id, 'nome': c.nome} for c in clientes]
        return jsonify(result)

    @bp.route('/api/cliente/<int:cliente_id>')
    @require_login
    def api_cliente(cliente_id):
        c = Cliente.query.get_or_404(cliente_id)
        dividas = []
        for d in c.dividas:
            pagamentos = [{'id': p.id, 'valor': p.valor, 'data': p.data_pagamento.isoformat(), 'meio': p.meio_pagamento} for p in d.pagamentos]
            reneg = [{'id': r.id, 'nova_data_venc': r.nova_data_venc.isoformat(), 'juros': r.juros_percent, 'data': r.data_reneg.isoformat()} for r in d.renegociacoes]
            dividas.append({'id': d.id, 'valor_original': d.valor_original, 'saldo': d.saldo_devedor, 'vencimento': d.data_vencimento.isoformat(), 'status': d.status, 'descricao': d.descricao, 'pagamentos': pagamentos, 'renegociacoes': reneg})

        data = {'id': c.id, 'nome': c.nome, 'cpf': c.cpf, 'celular': c.celular, 'endereco': c.endereco, 'nivel': c.nivel_confianca, 'limite': c.limite_credito, 'dividas': dividas}
        return jsonify(data)

    # ---------------- Clientes (CRUD) ----------------
    @bp.route('/clientes')
    @require_login
    def listar_clientes():
        clientes = Cliente.query.all()
        return render_template('clientes_list.html', clientes=clientes)

    @bp.route('/clientes/novo', methods=['GET', 'POST'])
    @require_login
    def novo_cliente():
        if request.method == 'POST':
            nome = request.form.get('nome')
            cpf = request.form.get('cpf')
            celular = request.form.get('celular')
            endereco = request.form.get('endereco')
            nivel = request.form.get('nivel') or 'Novo'
            limite = float(request.form.get('limite') or 200.0)

            cliente = Cliente(nome=nome, cpf=cpf, celular=celular, endereco=endereco, nivel_confianca=nivel, limite_credito=limite)
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso.')
            return redirect(url_for('main.listar_clientes'))

        return render_template('clientes_form.html')

    # ---------------- Usuários (admin) ----------------
    @bp.route('/admin/usuarios')
    @require_admin
    def admin_usuarios():
        usuarios = Usuario.query.all()
        return render_template('usuarios_list.html', usuarios=usuarios)

    @bp.route('/admin/usuarios/novo', methods=['GET', 'POST'])
    @require_admin
    def admin_novo_usuario():
        if request.method == 'POST':
            nome = request.form.get('nome')
            cpf = request.form.get('cpf')
            email = request.form.get('email')
            tipo = request.form.get('tipo') or 'Caixa'
            senha = request.form.get('senha')
            senha_hash = generate_password_hash(senha or '')

            usuario = Usuario(nome=nome, cpf=cpf, email=email, tipo=tipo, senha_hash=senha_hash)
            db.session.add(usuario)
            db.session.commit()
            flash('Usuário cadastrado com sucesso.')
            return redirect(url_for('main.admin_usuarios'))

        return render_template('usuarios_form.html')

    @bp.route('/admin/usuarios/<int:uid>/delete', methods=['POST'])
    @require_admin
    def admin_delete_usuario(uid):
        u = Usuario.query.get_or_404(uid)
        db.session.delete(u)
        db.session.commit()
        flash('Usuário removido.')
        return redirect(url_for('main.admin_usuarios'))

    # ---------------- Dívidas / Financeiro ----------------
    @bp.route('/dividas')
    @require_login
    def listar_dividas():
        dividas = Divida.query.all()
        return render_template('dividas_list.html', dividas=dividas)

    @bp.route('/dividas/novo', methods=['GET', 'POST'])
    @require_login
    def novo_divida():
        clientes = Cliente.query.all()
        preselect = request.args.get('cliente_id')
        cliente_nome = None
        
        if preselect:
            cliente_selecionado = Cliente.query.get(int(preselect))
            if cliente_selecionado:
                cliente_nome = cliente_selecionado.nome
        
        if request.method == 'POST':
            cliente_id = int(request.form.get('cliente_id'))
            valor = float(request.form.get('valor'))
            descricao = request.form.get('descricao') or ''
            prazo = int(request.form.get('prazo') or 0)

            cliente = Cliente.query.get(cliente_id)
            if not cliente:
                flash('Cliente não encontrado.')
                return redirect(url_for('main.novo_divida'))

            data_venc = date.today() + timedelta(days=prazo)

            # acumulativo: atualizar prazo das dívidas pendentes e registrar no histórico
            usuario_nome = session.get('user_nome', 'Sistema')
            pendentes = Divida.query.filter_by(cliente_id=cliente.id).filter(Divida.status != 'Paga').all()
            for d in pendentes:
                d.renegociar(data_venc, 0.0, usuario_nome)

            divida = Divida(cliente_id=cliente.id, valor_original=valor, saldo_devedor=valor, data_vencimento=data_venc, descricao=descricao)
            db.session.add(divida)
            db.session.commit()
            flash('Dívida registrada com sucesso.')
            return redirect(url_for('main.home'))

        return render_template('dividas_form.html', clientes=clientes, preselect=preselect, cliente_nome=cliente_nome)

    @bp.route('/pagamentos/novo', methods=['GET', 'POST'])
    @require_login
    def novo_pagamento():
        cliente_id = request.args.get('cliente_id', type=int)
        
        if cliente_id:
            cliente = Cliente.query.get_or_404(cliente_id)
            dividas = Divida.query.filter_by(cliente_id=cliente.id).filter(Divida.saldo_devedor > 0).all()
        else:
            cliente = None
            dividas = Divida.query.filter(Divida.saldo_devedor > 0).all()
        
        if request.method == 'POST':
            divida_id = int(request.form.get('divida_id'))
            valor = float(request.form.get('valor'))
            meio = request.form.get('meio')
            usuario = request.form.get('usuario') or session.get('user_nome', 'Operador')

            divida = Divida.query.get_or_404(divida_id)
            pagamento = Pagamento(divida_id=divida.id, valor=valor, meio_pagamento=meio, usuario_responsavel=usuario)
            divida.registrar_pagamento(pagamento)
            db.session.commit()
            flash('Pagamento registrado.')
            return redirect(url_for('main.home'))

        return render_template('pagamentos_form.html', dividas=dividas, cliente=cliente)

    @bp.route('/dividas/<int:divida_id>/pagar', methods=['GET', 'POST'])
    @require_login
    def pagar_divida(divida_id):
        divida = Divida.query.get_or_404(divida_id)
        if request.method == 'POST':
            valor = float(request.form.get('valor'))
            meio = request.form.get('meio')
            usuario = request.form.get('usuario') or session.get('user_nome', 'Operador')

            pagamento = Pagamento(divida_id=divida.id, valor=valor, meio_pagamento=meio, usuario_responsavel=usuario)
            divida.registrar_pagamento(pagamento)
            db.session.commit()
            flash('Pagamento registrado.')
            return redirect(url_for('main.listar_dividas'))

        return render_template('pagar_form.html', divida=divida)

    # ---------------- Relatórios ----------------
    @bp.route('/relatorios/dashboard')
    @require_login
    def relatorio_dashboard():
        dividas = Divida.query.all()
        hoje = date.today()
        total_a_receber = sum(d.saldo_devedor for d in dividas if d.status != 'Paga')
        total_vencido = sum(d.saldo_devedor for d in dividas if d.status != 'Paga' and d.data_vencimento < hoje)
        qtd_pagas = sum(1 for d in dividas if d.status == 'Paga')

        ranking = {}
        for d in dividas:
            if d.status == 'Paga':
                continue
            nome = d.cliente.nome
            ranking[nome] = ranking.get(nome, 0) + d.saldo_devedor

        ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

        return render_template('relatorios_dashboard.html', total_a_receber=total_a_receber, total_vencido=total_vencido, qtd_pagas=qtd_pagas, ranking=ranking_ordenado[:5])

    @bp.route('/relatorios/extrato', methods=['GET', 'POST'])
    @require_login
    def relatorio_extrato():
        cliente = None
        dividas_cliente = []
        total = 0.0
        if request.method == 'POST':
            termo = request.form.get('termo')
            if termo.isdigit():
                cliente = Cliente.query.get(int(termo))
            else:
                cliente = Cliente.query.filter(Cliente.nome.ilike(f"%{termo}%")).first()

            if cliente:
                dividas_cliente = Divida.query.filter_by(cliente_id=cliente.id).all()
                total = sum(d.saldo_devedor for d in dividas_cliente)

        return render_template('relatorios_extrato.html', cliente=cliente, dividas=dividas_cliente, total=total)

    app.register_blueprint(bp)
