from datetime import date

class Pagamento:
    def __init__(self, id_pagamento, divida_vinculada, valor, meio_pagamento, usuario_responsavel):
        self.id_pagamento = id_pagamento
        self.divida_vinculada = divida_vinculada
        self.valor = valor
        self.data_pagamento = date.today()
        self.meio_pagamento = meio_pagamento
        self.usuario_responsavel = usuario_responsavel

from datetime import date

class Renegociacao:
    """
    Registra o evento de renegociação de uma dívida.
    Fonte: Diagrama de Classes e Requisitos.
    """
    def __init__(self, id_reneg, divida_vinculada, nova_data_venc, juros_percent, usuario_responsavel):
        self.id_reneg = id_reneg
        self.divida_vinculada = divida_vinculada
        self.nova_data_venc = nova_data_venc
        self.juros_percent = juros_percent
        self.data_reneg = date.today()
        self.usuario_responsavel = usuario_responsavel

class Divida:
    def __init__(self, id_divida, cliente, valor_original, data_vencimento, descricao=""):
        self.id_divida = id_divida
        self.cliente = cliente
        self.valor_original = valor_original
        self.data_venda = date.today()
        self.data_vencimento = data_vencimento
        self.descricao = descricao
        self.status = "Pendente"
        
        self.saldo_devedor = valor_original
        
        self.historico_pagamentos = [] 
        self.historico_renegociacoes = [] # Nova lista para guardar histórico 

    def aplicar_pagamento(self, pagamento):
        self.historico_pagamentos.append(pagamento)
        self.saldo_devedor -= pagamento.valor
        if self.saldo_devedor <= 0:
            self.saldo_devedor = 0.0
            self.status = "Paga"
            print(f"Dívida de {self.cliente.nome} quitada!")
        else:
            print(f"Restam R${self.saldo_devedor:.2f}")

    def renegociar(self, nova_data, juros_percent, usuario_responsavel):
        """
        Aplica novos prazos e juros à dívida.
        Fonte: Requisito de Renegociação.
        """
        id_reneg = len(self.historico_renegociacoes) + 1
        renegoc = Renegociacao(id_reneg, self, nova_data, juros_percent, usuario_responsavel)
        self.historico_renegociacoes.append(renegoc)
        
        acrescimo = self.saldo_devedor * (juros_percent / 100)
        self.saldo_devedor += acrescimo
        
        self.data_vencimento = nova_data
        self.status = "Renegociada" 
        
        print(f"--- RENEGOCIAÇÃO CONCLUÍDA ---")
        print(f"Juros aplicados: {juros_percent}% (+ R${acrescimo:.2f})")
        print(f"Novo Saldo Devedor: R${self.saldo_devedor:.2f}")
        print(f"Nova Data de Vencimento: {self.data_vencimento}")