"""
Rotas do SGM - Sistema de Gerenciamento de Mercearia

Organização:
1. Decoradores de segurança (require_login, require_admin)
2. Autenticação (login, logout)
3. Dashboard principal
4. API para busca de clientes
5. CRUD de Clientes
6. CRUD de Usuários (Admin)
7. Gestão Financeira (Dívidas, Pagamentos, Renegociações)
8. Relatórios
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from web.models import db, Cliente, Usuario, Divida, Pagamento, Renegociacao, Parcela
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from werkzeug.security import check_password_hash, generate_password_hash
from collections import defaultdict
import calendar


def register_routes(app):
    """Registra todas as rotas da aplicação"""
    bp = Blueprint('main', __name__)

    # ==================== DECORADORES DE SEGURANÇA ====================
    
    def require_login(fn):
        """Decorator: requer que o usuário esteja logado"""
        def wrapper(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('main.login'))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper

    def require_admin(fn):
        """Decorator: requer que o usuário seja administrador"""
        def wrapper(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('main.login'))
            if session.get('user_tipo') != 'Administrador':
                flash('Acesso negado: apenas administradores.')
                return redirect(url_for('main.home'))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper

    # ==================== AUTENTICAÇÃO ====================
    @bp.route('/', methods=['GET', 'POST'])
    def login():
        """Página de login do sistema"""
        if request.method == 'POST':
            usuario = request.form.get('usuario')
            senha = request.form.get('senha')

            # Busca usuário por nome ou email
            user = Usuario.query.filter(
                (Usuario.nome == usuario) | (Usuario.email == usuario)
            ).first()
            
            # Valida senha
            if user and check_password_hash(user.senha_hash, senha or ''):
                # Salva dados na sessão
                session['user_id'] = user.id
                session['user_nome'] = user.nome
                session['user_tipo'] = user.tipo
                return redirect(url_for('main.home'))
            
            flash('Credenciais inválidas')
        
        return render_template('login.html')

    @bp.route('/logout')
    def logout():
        """Faz logout limpando a sessão"""
        session.clear()
        return redirect(url_for('main.login'))

    # ==================== DASHBOARD PRINCIPAL ====================
    @bp.route('/home')
    @require_login
    def home():
        """
        Dashboard principal
        - Admin: exibe dashboard completo com KPIs e gráficos
        - Caixa: tela básica para operações
        """
        tipo = session.get('user_tipo')
        
        # Se vier com cliente_id, renderiza página vazia para o JavaScript preencher
        if request.args.get('cliente_id'):
            return render_template('home.html', dashboard=False, hide_aside=False)
        
        if tipo == 'Administrador':
            # Carrega todos os dados necessários
            dividas = Divida.query.all()
            pagamentos = Pagamento.query.all()
            hoje = date.today()

            # ===== KPIs (Indicadores) =====
            total_a_receber = sum(d.saldo_devedor for d in dividas if d.status != 'Paga')
            total_vencido = sum(
                d.saldo_devedor for d in dividas 
                if d.status != 'Paga' and d.data_vencimento <= hoje
            )
            qtd_pagas = sum(1 for d in dividas if d.status == 'Paga')
            qtd_vencidas = sum(1 for d in dividas if d.status != 'Paga' and d.data_vencimento < hoje)
            qtd_abertas = sum(1 for d in dividas if d.status != 'Paga' and d.data_vencimento >= hoje)

            # ===== Ranking: Top 5 devedores =====
            ranking = {}
            for d in dividas:
                if d.status == 'Paga':
                    continue
                nome = d.cliente.nome
                ranking[nome] = ranking.get(nome, 0) + d.saldo_devedor
            
            ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:5]
            top_labels = [n for n, _ in ranking_ordenado]
            top_values = [v for _, v in ranking_ordenado]

            # ===== Contagem por Status =====
            pagas_ct = 0
            renegociadas_ct = 0
            vencidas_ct = 0
            em_dia_ct = 0
            
            for d in dividas:
                if d.status == 'Paga' or d.saldo_devedor <= 0:
                    pagas_ct += 1
                elif d.data_vencimento <= hoje and d.saldo_devedor > 0:
                    # Vencida tem prioridade sobre status (inclui hoje)
                    vencidas_ct += 1
                elif d.status == 'Renegociada' and d.saldo_devedor > 0:
                    renegociadas_ct += 1
                elif d.saldo_devedor > 0:
                    em_dia_ct += 1

            # ===== Pagamentos por Meio =====
            meio_map = {}
            for p in pagamentos:
                meio = p.meio_pagamento or 'Outro'
                meio_map[meio] = meio_map.get(meio, 0) + 1
            meio_labels = list(meio_map.keys())
            meio_values = list(meio_map.values())

            # ===== Dívidas por Mês (últimos 6 meses) =====
            by_month = defaultdict(float)
            for d in dividas:
                if d.data_venda:
                    ano, mes = d.data_venda.year, d.data_venda.month
                    by_month[(ano, mes)] += float(d.valor_original or 0)
            
            # Monta labels e valores dos últimos 6 meses
            labels_month = []
            values_month = []
            ref = date(hoje.year, hoje.month, 1)
            
            for i in range(5, -1, -1):
                ano = ref.year
                mes = ref.month - i
                # Ajusta ano se mês for negativo
                while mes <= 0:
                    ano -= 1
                    mes += 12
                
                labels_month.append(f"{calendar.month_abbr[mes]}/{str(ano)[-2:]}")
                values_month.append(round(by_month.get((ano, mes), 0.0), 2))

            # ===== Lista de Dívidas Vencidas =====
            dividas_vencidas = []
            for d in dividas:
                if d.status != 'Paga' and d.saldo_devedor > 0 and d.data_vencimento <= hoje:
                    dividas_vencidas.append({
                        'id': d.id,
                        'cliente_nome': d.cliente.nome,
                        'descricao': d.descricao or 'Sem descrição',
                        'saldo': d.saldo_devedor,
                        'vencimento': d.data_vencimento
                    })
            # Ordenar por vencimento (mais antigas primeiro)
            dividas_vencidas.sort(key=lambda x: x['vencimento'])

            return render_template(
                'home.html',
                dashboard=True,
                total_a_receber=total_a_receber,
                total_vencido=total_vencido,
                qtd_pagas=qtd_pagas,
                qtd_vencidas=qtd_vencidas,
                qtd_abertas=qtd_abertas,
                ranking=ranking_ordenado,
                dividas_vencidas=dividas_vencidas,
                # dados para gráficos
                top_labels=top_labels,
                top_values=top_values,
                status_labels=['Pagas', 'Em dia', 'Renegociadas', 'Vencidas'],
                status_values=[pagas_ct, em_dia_ct, renegociadas_ct, vencidas_ct],
                meio_labels=meio_labels,
                meio_values=meio_values,
                month_labels=labels_month,
                month_values=values_month,
            )

        # Caixa: tela simples sem dashboard
        return render_template('home.html', dashboard=False)

    # ==================== API - BUSCA DE CLIENTES ====================
    
    @bp.route('/api/clientes')
    @require_login
    def api_clientes():
        """API: Retorna lista de clientes (com busca opcional)"""
        q = request.args.get('q', '').strip()
        
        if q:
            # Busca por nome parcial
            clientes = Cliente.query.filter(Cliente.nome.ilike(f'%{q}%')).all()
        else:
            # Retorna todos ordenados
            clientes = Cliente.query.order_by(Cliente.nome).all()
        
        result = [{'id': c.id, 'nome': c.nome} for c in clientes]
        return jsonify(result)

    @bp.route('/api/cliente/<int:cliente_id>')
    @require_login
    def api_cliente(cliente_id):
        """API: Retorna dados completos de um cliente (incluindo dívidas)"""
        c = Cliente.query.get_or_404(cliente_id)
        
        # Monta lista de dívidas com pagamentos e renegociações
        dividas = []
        for d in c.dividas:
            pagamentos = [
                {
                    'id': p.id,
                    'valor': p.valor,
                    'data': p.data_pagamento.isoformat(),
                    'meio': p.meio_pagamento
                }
                for p in d.pagamentos
            ]
            
            reneg = [
                {
                    'id': r.id,
                    'nova_data_venc': r.nova_data_venc.isoformat(),
                    'juros': r.juros_percent,
                    'data': r.data_reneg.isoformat()
                }
                for r in d.renegociacoes
            ]
            
            parcelas = [
                {
                    'numero': p.numero_parcela,
                    'valor_parcela': p.valor_parcela,
                    'data_vencimento': p.data_vencimento.isoformat(),
                    'status': p.status,
                    'valor_pago': p.valor_pago
                }
                for p in d.parcelas
            ]
            
            dividas.append({
                'id': d.id,
                'valor_original': d.valor_original,
                'saldo': d.saldo_devedor,
                'vencimento': d.data_vencimento.isoformat(),
                'status': d.status,
                'descricao': d.descricao,
                'parcelado': d.parcelado,
                'num_parcelas': d.num_parcelas,
                'juros_parcelamento': d.juros_parcelamento,
                'pagamentos': pagamentos,
                'renegociacoes': reneg,
                'parcelas': parcelas
            })

        # Monta resposta completa
        data = {
            'id': c.id,
            'nome': c.nome,
            'cpf': c.cpf,
            'celular': c.celular,
            'endereco': c.endereco,
            'nivel': c.nivel_confianca,
            'limite': c.limite_credito,
            'dividas': dividas
        }
        return jsonify(data)

    # ==================== CRUD - CLIENTES ====================
    @bp.route('/clientes')
    @require_login
    def listar_clientes():
        """Lista todos os clientes cadastrados"""
        clientes = Cliente.query.order_by(Cliente.nome).all()
        return render_template('clientes_list.html', clientes=clientes)

    @bp.route('/clientes/novo', methods=['GET', 'POST'])
    @require_login
    def novo_cliente():
        """Cadastro de novo cliente"""
        if request.method == 'POST':
            nome = request.form.get('nome')
            cpf = request.form.get('cpf')
            celular = request.form.get('celular')
            endereco = request.form.get('endereco')
            nivel = request.form.get('nivel') or 'Novo'
            limite = float(request.form.get('limite') or 200.0)

            # Valida se cliente já existe
            if Cliente.query.filter_by(nome=nome).first():
                flash('Erro: Já existe um cliente cadastrado com este nome.')
                return render_template('clientes_form.html')

            # Cria e salva novo cliente
            cliente = Cliente(
                nome=nome,
                cpf=cpf,
                celular=celular,
                endereco=endereco,
                nivel_confianca=nivel,
                limite_credito=limite
            )
            db.session.add(cliente)
            db.session.commit()
            
            flash('Cliente cadastrado com sucesso.')
            return redirect(url_for('main.home') + f'?cliente_id={cliente.id}')

        return render_template('clientes_form.html')

    @bp.route('/clientes/<int:cliente_id>/apagar', methods=['POST'])
    @require_admin
    def apagar_cliente(cliente_id):
        """Apaga cliente e todos os dados associados (apenas admin)"""
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Cascade delete já configurado no modelo, mas fazendo manualmente por garantia
        dividas = Divida.query.filter_by(cliente_id=cliente.id).all()
        for d in dividas:
            Pagamento.query.filter_by(divida_id=d.id).delete()
            Renegociacao.query.filter_by(divida_id=d.id).delete()
        Divida.query.filter_by(cliente_id=cliente.id).delete()
        
        # Remove cliente
        db.session.delete(cliente)
        db.session.commit()
        
        return '', 200

    # ==================== CRUD - USUÁRIOS (ADMIN) ====================
    @bp.route('/admin/usuarios')
    @require_admin
    def admin_usuarios():
        """Lista todos os usuários do sistema"""
        usuarios = Usuario.query.order_by(Usuario.nome).all()
        return render_template('usuarios_list.html', usuarios=usuarios)

    @bp.route('/admin/config')
    @require_admin
    def admin_config():
        """Página de configurações administrativas"""
        clientes = Cliente.query.order_by(Cliente.nome).all()
        usuarios = Usuario.query.order_by(Usuario.nome).all()
        return render_template(
            'admin_config.html',
            clientes=clientes,
            usuarios=usuarios,
            hide_aside=True  # Oculta a sidebar de clientes nesta página
        )

    @bp.route('/admin/usuarios/novo', methods=['GET', 'POST'])
    @require_admin
    def admin_novo_usuario():
        """Cadastro de novo usuário (funcionário)"""
        if request.method == 'POST':
            nome = request.form.get('nome')
            cpf = request.form.get('cpf')
            email = request.form.get('email')
            tipo = request.form.get('tipo') or 'Caixa'
            senha = request.form.get('senha')
            
            # Valida email único
            if email and Usuario.query.filter_by(email=email).first():
                flash('Erro: Já existe um usuário cadastrado com este email.')
                return render_template('usuarios_form.html')
            
            # Valida nome único
            if Usuario.query.filter_by(nome=nome).first():
                flash('Erro: Já existe um usuário cadastrado com este nome.')
                return render_template('usuarios_form.html')
            
            # Cria e salva usuário
            usuario = Usuario(
                nome=nome,
                cpf=cpf,
                email=email,
                tipo=tipo,
                senha_hash=generate_password_hash(senha or '')
            )
            db.session.add(usuario)
            db.session.commit()
            
            flash('Usuário cadastrado com sucesso.')
            return redirect(url_for('main.admin_usuarios'))

        return render_template('usuarios_form.html')

    @bp.route('/admin/usuarios/<int:uid>/delete', methods=['POST'])
    @require_admin
    def admin_delete_usuario(uid):
        """Remove um usuário do sistema"""
        usuario = Usuario.query.get_or_404(uid)
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário removido.')
        return redirect(url_for('main.admin_usuarios'))

    # ==================== GESTÃO FINANCEIRA ====================
    @bp.route('/dividas')
    @require_login
    def listar_dividas():
        """Lista todas as dívidas do sistema"""
        dividas = Divida.query.order_by(Divida.data_vencimento).all()
        return render_template('dividas_list.html', dividas=dividas)

    @bp.route('/dividas/novo', methods=['GET', 'POST'])
    @require_login
    def novo_divida():
        """Registra uma nova dívida (venda a prazo)"""
        clientes = Cliente.query.order_by(Cliente.nome).all()
        preselect = request.args.get('cliente_id')
        cliente_nome = None
        
        # Se vier de um cliente específico, pré-seleciona
        if preselect:
            cliente_selecionado = Cliente.query.get(int(preselect))
            if cliente_selecionado:
                cliente_nome = cliente_selecionado.nome
        
        if request.method == 'POST':
            cliente_id = int(request.form.get('cliente_id'))
            valor = float(request.form.get('valor'))
            descricao = request.form.get('descricao') or ''
            prazo = int(request.form.get('prazo') or 0)
            num_parcelas = int(request.form.get('num_parcelas') or 1)
            juros_parcelamento = float(request.form.get('juros_parcelamento') or 0.0)

            cliente = Cliente.query.get(cliente_id)
            if not cliente:
                flash('Cliente não encontrado.')
                return redirect(url_for('main.novo_divida'))

            # COMPORTAMENTO ACUMULATIVO:
            # Atualiza prazo de todas as dívidas pendentes para o mesmo prazo da nova
            usuario_nome = session.get('user_nome', 'Sistema')
            pendentes = Divida.query.filter_by(cliente_id=cliente.id)\
                                    .filter(Divida.status != 'Paga').all()
            
            # Calcula valor total com juros (se parcelado)
            valor_total = valor
            if num_parcelas > 1 and juros_parcelamento > 0:
                valor_total = valor * (1 + juros_parcelamento / 100)
            
            # Cria nova dívida
            divida = Divida(
                cliente_id=cliente.id,
                valor_original=valor,
                saldo_devedor=valor_total,
                data_vencimento=date.today() + timedelta(days=prazo),
                descricao=descricao,
                parcelado=(num_parcelas > 1),
                num_parcelas=num_parcelas,
                juros_parcelamento=juros_parcelamento if num_parcelas > 1 else 0.0
            )
            db.session.add(divida)
            db.session.flush()  # Garante que divida.id está disponível
            
            # Se parcelado, cria as parcelas
            if num_parcelas > 1:
                from web.models import Parcela
                valor_parcela = valor_total / num_parcelas
                
                for i in range(1, num_parcelas + 1):
                    # Vencimento: mesmo dia do próximo mês (1ª parcela = +1 mês, 2ª = +2 meses, etc)
                    vencimento_parcela = date.today() + relativedelta(months=i)
                    parcela = Parcela(
                        divida_id=divida.id,
                        numero_parcela=i,
                        valor_parcela=valor_parcela,
                        data_vencimento=vencimento_parcela,
                        status='Pendente'
                    )
                    db.session.add(parcela)
                
                # Atualiza data de vencimento da dívida para a última parcela
                divida.data_vencimento = date.today() + relativedelta(months=num_parcelas)
            
            # Renegocia dívidas pendentes (após criar a nova)
            for d in pendentes:
                d.renegociar(divida.data_vencimento, 0.0, usuario_nome)
            
            db.session.commit()
            
            if num_parcelas > 1:
                flash(f'Dívida registrada com sucesso! Parcelada em {num_parcelas}x de R$ {valor_parcela:.2f}')
            else:
                flash('Dívida registrada com sucesso.')
            return redirect(url_for('main.home') + f'?cliente_id={cliente_id}')

        return render_template(
            'dividas_form.html',
            clientes=clientes,
            preselect=preselect,
            cliente_nome=cliente_nome
        )

    @bp.route('/pagamentos/novo', methods=['GET', 'POST'])
    @require_login
    def novo_pagamento():
        """Registra um novo pagamento em uma dívida"""
        cliente_id = request.args.get('cliente_id', type=int)
        
        # Filtra dívidas do cliente ou mostra todas
        if cliente_id:
            cliente = Cliente.query.get_or_404(cliente_id)
            dividas = Divida.query.filter_by(cliente_id=cliente.id)\
                                  .filter(Divida.saldo_devedor > 0).all()
        else:
            cliente = None
            dividas = Divida.query.filter(Divida.saldo_devedor > 0).all()
        
        if request.method == 'POST':
            divida_id = int(request.form.get('divida_id'))
            valor = float(request.form.get('valor'))
            meio = request.form.get('meio')
            usuario = request.form.get('usuario') or session.get('user_nome', 'Operador')
            parcela_id = request.form.get('parcela_id', type=int)

            # Registra o pagamento
            divida = Divida.query.get_or_404(divida_id)
            
            # Se for dívida parcelada, valida a parcela
            if divida.parcelado and parcela_id:
                parcela = Parcela.query.get_or_404(parcela_id)
                
                # Valida se o valor não excede o restante da parcela (com margem de 1 centavo)
                valor_restante = parcela.valor_parcela - parcela.valor_pago
                if valor > valor_restante + 0.01:
                    flash(f'Valor excede o restante da parcela (R$ {valor_restante:.2f})')
                    return redirect(url_for('main.novo_pagamento', cliente_id=cliente_id))
                
                # Atualiza a parcela
                valor_efetivo = min(valor, valor_restante)
                parcela.valor_pago += valor_efetivo
                if parcela.valor_pago >= parcela.valor_parcela - 0.01:
                    parcela.status = 'Paga'
                    parcela.valor_pago = parcela.valor_parcela
                
                db.session.add(parcela)
            
            pagamento = Pagamento(
                divida_id=divida.id,
                valor=valor,
                meio_pagamento=meio,
                usuario_responsavel=usuario
            )
            divida.registrar_pagamento(pagamento)
            db.session.commit()
            
            flash('Pagamento registrado com sucesso.')
            return redirect(url_for('main.home') + f'?cliente_id={divida.cliente_id}')

        # Preparar dados das dívidas com parcelas serializadas
        dividas_data = []
        for d in dividas:
            parcelas_list = []
            if d.parcelado:
                for p in d.parcelas:
                    parcelas_list.append({
                        'id': p.id,
                        'numero': p.numero_parcela,
                        'valor_parcela': p.valor_parcela,
                        'data_vencimento': p.data_vencimento.isoformat(),
                        'status': p.status,
                        'valor_pago': p.valor_pago
                    })
            
            dividas_data.append({
                'id': d.id,
                'descricao': d.descricao,
                'saldo_devedor': d.saldo_devedor,
                'parcelado': d.parcelado,
                'parcelas': parcelas_list
            })
        
        return render_template('pagamentos_form.html', dividas=dividas_data, cliente=cliente)

    @bp.route('/dividas/<int:divida_id>/pagar', methods=['GET', 'POST'])
    @require_login
    def pagar_divida(divida_id):
        """Formulário para pagar uma dívida específica"""
        divida = Divida.query.get_or_404(divida_id)
        
        if request.method == 'POST':
            valor = float(request.form.get('valor'))
            meio = request.form.get('meio')
            usuario = request.form.get('usuario') or session.get('user_nome', 'Operador')

            # Registra pagamento
            pagamento = Pagamento(
                divida_id=divida.id,
                valor=valor,
                meio_pagamento=meio,
                usuario_responsavel=usuario
            )
            divida.registrar_pagamento(pagamento)
            db.session.commit()
            
            flash('Pagamento registrado com sucesso.')
            return redirect(url_for('main.listar_dividas'))

        return render_template('pagar_form.html', divida=divida)

    @bp.route('/dividas/<int:divida_id>/renegociar', methods=['GET', 'POST'])
    @require_login
    def renegociar_divida(divida_id):
        """Renegocia prazo e juros de uma dívida"""
        divida = Divida.query.get_or_404(divida_id)
        
        if request.method == 'POST':
            prazo_dias = int(request.form.get('prazo_dias') or 30)
            juros = float(request.form.get('juros') or 0.0)
            usuario = session.get('user_nome', 'Operador')
            
            # Aplica renegociação
            nova_data = date.today() + timedelta(days=prazo_dias)
            divida.renegociar(nova_data, juros, usuario)
            db.session.commit()
            
            flash('Dívida renegociada com sucesso.')
            return redirect(url_for('main.home') + f'?cliente_id={divida.cliente_id}')
        
        return render_template('renegociar_form.html', divida=divida)

    @bp.route('/dividas/<int:divida_id>/apagar', methods=['POST'])
    @require_login
    def apagar_divida(divida_id):
        """
        Apaga uma dívida do sistema
        - Admin: pode apagar diretamente
        - Caixa: precisa informar credenciais de admin
        """
        divida = Divida.query.get_or_404(divida_id)
        
        # Se for caixista, valida credenciais de admin
        if session.get('user_tipo') != 'Administrador':
            data = request.get_json()
            if not data:
                return 'Credenciais de administrador necessárias', 400
            
            usuario = data.get('usuario')
            senha = data.get('senha')
            
            # Valida admin
            admin = Usuario.query.filter(
                (Usuario.nome == usuario) | (Usuario.email == usuario)
            ).first()
            
            if not admin or admin.tipo != 'Administrador' or \
               not check_password_hash(admin.senha_hash, senha):
                return 'Usuário/senha inválidos ou não é administrador', 403
        
        # Remove pagamentos e renegociações associados
        Pagamento.query.filter_by(divida_id=divida.id).delete()
        Renegociacao.query.filter_by(divida_id=divida.id).delete()
        
        # Remove a dívida
        db.session.delete(divida)
        db.session.commit()
        
        return '', 200

    # ==================== RELATÓRIOS ====================
    @bp.route('/relatorios/dashboard')
    @require_login
    def relatorio_dashboard():
        """Relatório: Dashboard consolidado (versão simplificada)"""
        dividas = Divida.query.all()
        hoje = date.today()
        
        # KPIs básicos
        total_a_receber = sum(d.saldo_devedor for d in dividas if d.status != 'Paga')
        total_vencido = sum(
            d.saldo_devedor for d in dividas
            if d.status != 'Paga' and d.data_vencimento < hoje
        )
        qtd_pagas = sum(1 for d in dividas if d.status == 'Paga')

        # Ranking de devedores
        ranking = {}
        for d in dividas:
            if d.status == 'Paga':
                continue
            nome = d.cliente.nome
            ranking[nome] = ranking.get(nome, 0) + d.saldo_devedor

        ranking_ordenado = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

        return render_template(
            'relatorios_dashboard.html',
            total_a_receber=total_a_receber,
            total_vencido=total_vencido,
            qtd_pagas=qtd_pagas,
            ranking=ranking_ordenado[:5]
        )

    @bp.route('/relatorios/extrato', methods=['GET', 'POST'])
    @require_login
    def relatorio_extrato():
        """Relatório: Extrato de um cliente específico"""
        cliente = None
        dividas_cliente = []
        total = 0.0
        
        if request.method == 'POST':
            termo = request.form.get('termo')
            
            # Busca por ID ou nome
            if termo.isdigit():
                cliente = Cliente.query.get(int(termo))
            else:
                cliente = Cliente.query.filter(Cliente.nome.ilike(f"%{termo}%")).first()

            # Carrega dívidas do cliente
            if cliente:
                dividas_cliente = Divida.query.filter_by(cliente_id=cliente.id).all()
                total = sum(d.saldo_devedor for d in dividas_cliente)

        return render_template(
            'relatorios_extrato.html',
            cliente=cliente,
            dividas=dividas_cliente,
            total=total
        )

    # Registra todas as rotas no Flask
    app.register_blueprint(bp)
