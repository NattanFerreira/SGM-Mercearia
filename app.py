"""
SGM - Sistema de Gerenciamento de Mercearia
Aplicação Flask para controle de vendas fiado (a prazo)

Funcionalidades:
- Gerenciamento de clientes
- Registro de dívidas (vendas a prazo)
- Controle de pagamentos
- Renegociação de dívidas
- Dashboard com análises e relatórios
- Sistema de autenticação (Admin/Caixa)
"""

from flask import Flask
from web.models import db, Usuario
from werkzeug.security import generate_password_hash
from web.routes import register_routes


def create_app():
    """
    Factory function para criar e configurar a aplicação Flask
    
    Returns:
        Flask app configurada e pronta para uso
    """
    app = Flask(__name__)
    
    # Configurações do banco de dados
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sgm.db'  # Banco SQLite local
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa warnings desnecessários
    app.config['SECRET_KEY'] = 'troque-esta-chave-por-uma-segura'  # Para sessões

    # Inicializa o banco de dados
    db.init_app(app)

    # Registra todas as rotas da aplicação
    register_routes(app)

    # Cria as tabelas e usuário admin padrão
    with app.app_context():
        db.create_all()
        
        # Cria usuário administrador padrão se não existir
        if not Usuario.query.filter_by(nome='adm').first():
            admin = Usuario(
                nome='adm',
                cpf=None,
                email='adm@sgm.com',
                senha_hash=generate_password_hash('adm'),
                tipo='Administrador'
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Usuário administrador criado: adm/adm")

    return app


if __name__ == '__main__':
    # Cria e executa a aplicação
    app = create_app()
    print("\n" + "="*50)
    print("SGM - Sistema de Gerenciamento de Mercearia")
    print("="*50)
    print("➜ Acesse: http://127.0.0.1:5000")
    print("➜ Login padrão: adm / adm")
    print("="*50 + "\n")
    app.run(debug=True)
