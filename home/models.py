from django.db import models
from django.contrib.auth.models import User

# CRIAÇÃO DE TABELAS
class produtos(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True, verbose_name='ID do Produto')
    tipo = models.IntegerField(verbose_name='Tipo do Produto')
    nome = models.CharField(max_length=100, verbose_name='Nome do Produto')
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preco')
    medida = models.CharField(max_length=5, verbose_name='Unidade de Medida')
    quantidade = models.IntegerField(verbose_name='Quantidade em Estoque')
    created_prod = models.DateTimeField(auto_now_add=True, null=True)
    update_prod = models.DateTimeField(auto_now=True)

class clientes(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    id_cliente = models.AutoField(primary_key=True, verbose_name='ID do cliente')
    nome_cliente = models.CharField(max_length=100, verbose_name='Nome do cliente')
    contato = models.CharField(max_length=11, blank=True, null=True, verbose_name='telefone celular')
    created_cad = models.DateTimeField(auto_now_add=True, null=True)
    update_cad = models.DateTimeField(auto_now=True)

class Cesta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cliente = models.ForeignKey(clientes, on_delete=models.CASCADE, related_name='cesta_set')
    produto = models.ForeignKey(produtos, on_delete=models.DO_NOTHING)
    quantidade = models.IntegerField()
    preco_unit = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} - Cliente: {self.cliente.nome_cliente}"

class vendas(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True, verbose_name='ID da venda')
    id_cliente = models.ForeignKey(clientes, on_delete=models.DO_NOTHING)
    data_hora = models.DateTimeField(auto_now_add=True, null=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='valor total')
    desconto = models.IntegerField(verbose_name='desconto')

class itens_venda(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True, verbose_name='ID do item vendas')
    id_vendas = models.ForeignKey(vendas, on_delete=models.DO_NOTHING)
    prod_id = models.ForeignKey(produtos, on_delete=models.DO_NOTHING)
    quantidade = models.IntegerField(verbose_name='Quantidade vendido')
    preco_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço unitario')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal')

class pagamentos(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True, verbose_name='ID do pagamento')
    id_vendas = models.ForeignKey(vendas, on_delete=models.DO_NOTHING)
    forma_pag = models.IntegerField(verbose_name='Forma de pagamento')
    valor_pag = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='valor pago')
    troco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='valor pago')