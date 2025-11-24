from flask import Flask
from web.models import db, Usuario
from werkzeug.security import generate_password_hash
from web.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sgm.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'troque-esta-chave-por-uma-segura'

    db.init_app(app)

    register_routes(app)

    with app.app_context():
        db.create_all()
        # criar usuário inicial de teste (admin) se não existir
        if not Usuario.query.filter_by(nome='adm').first():
            adm = Usuario(nome='adm', cpf=None, email='adm', senha_hash=generate_password_hash('adm'), tipo='Administrador')
            db.session.add(adm)
            db.session.commit()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
