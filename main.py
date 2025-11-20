from controles.controle_usuarios import cadastrar_usuario, listar_usuarios
from controles.controle_clientes import cadastrar_cliente, listar_clientes
from controles.controle_financeiro import lancar_divida, listar_dividas, registrar_pagamento, realizar_renegociacao
from controles.controle_relatorios import exibir_dashboard, gerar_extrato_cliente
from utils.utils import limpar_tela


def menu_principal():
    while True:
        limpar_tela() 
        print("=== SGM MERCEARIA ===")
        print("1. Usuarios")
        print("2. Clientes")
        print("3. Financeiro (Dividas/Pagamentos)")
        print("4. Relatorios e Dashboard")
        print("5. Sair")
        
        opcao = input("Opcao: ")
        
        if opcao == "1":
            limpar_tela()
            print("--- USUARIOS ---")
            print("A - Cadastrar")
            print("B - Listar")
            sub = input("Escolha: ").upper()
            if sub == "A": cadastrar_usuario()
            elif sub == "B": listar_usuarios()
            
        elif opcao == "2":
            limpar_tela()
            print("--- CLIENTES ---")
            print("A - Cadastrar")
            print("B - Listar")
            sub = input("Escolha: ").upper()
            if sub == "A": cadastrar_cliente()
            elif sub == "B": listar_clientes()
            
        elif opcao == "3":
            limpar_tela()
            print("--- FINANCEIRO ---")
            print("A - Lancar Nova Divida")
            print("B - Listar Todas as Dividas")
            print("C - Registrar Pagamento")
            print("D - Renegociar Divida")
            sub = input("Escolha: ").upper()
            
            if sub == "A": lancar_divida()
            elif sub == "B": listar_dividas()
            elif sub == "C": registrar_pagamento()
            elif sub == "D": realizar_renegociacao()

        elif opcao == "4":
            limpar_tela()
            print("--- PAINEL GERENCIAL ---")
            print("A - Dashboard (Visao Geral)")
            print("B - Extrato de Cliente")
            sub = input("Escolha: ").upper()
            
            if sub == "A":
                exibir_dashboard()
            elif sub == "B":
                gerar_extrato_cliente()
                
        elif opcao == "5":
            print("Encerrando sistema...")
            break
        else:
            input("Opcao invalida. Pressione Enter...")

if __name__ == "__main__":
    menu_principal()