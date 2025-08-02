from django.shortcuts import render, redirect, get_object_or_404

from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.utils import timezone
from decimal import Decimal

from .models import produtos, clientes, Cesta, vendas, itens_venda, pagamentos
from .forms import Prod_Form, Cliente_Form
from django import forms
from django.contrib import messages

# NOTA DE ATUALIZAÇÃO FUTURA: ADICIONAR PAGINAÇÃO NA LISTA DE PRODUTOS E CLIENTES. LINK VIDEO: https://www.youtube.com/watch?v=RVTUugdKY9o&list=PLnDvRpP8BnewqnMzRnBT5LeTpld5bMvsj&index=13&ab_channel=MatheusBattisti-HoradeCodar

def home(request):

    return render(request, 'visual/home.html')






def relatorios(request):
    
    return render(request, 'visual/relatorios.html')


# FUNÇÕES DA PAGINA ESTOQUE

def estoque(request):
    # Exibir todos os produtos ja cadastrados em uma nova pagina
    todos_produtos = produtos.objects.all()
    
    lista = {
        'estoque': todos_produtos
    }
    # Retorna os dados para a pagina de listagem de produtos
    return render(request, 'visual/estoque.html', lista)



def add_produto(request):
    if request.method == 'POST':
        form = Prod_Form(request.POST)

        if form.is_valid():
            novo_prod = form.save(commit=False)
            novo_prod.done = 'doing'
            novo_prod.save()
            return redirect('/estoque')

    else:
        form = Prod_Form()
        return render(request,'visual/add_prod.html', {'form': form})
    
def delete_produto(request, id):
    produto = get_object_or_404(produtos, id=id)
    produto.delete()
    messages.success(request, 'Produto deletado com sucesso!')
    return redirect('/estoque')

def edit_produto(request, id):
    prod_edit = get_object_or_404(produtos, id=id)
    form = Prod_Form(instance=prod_edit)

    contexto = {
        'form':form,
        'prod_edit': prod_edit,
    }
    if(request.method == 'POST'):
        form = Prod_Form(request.POST, instance=prod_edit)

        if(form.is_valid()):
            prod_edit.save()
            return redirect('/estoque')
        else:
            return render(request, 'visual/edit_prod.html', contexto)
    else:
        return render(request, 'visual/edit_prod.html', contexto)


# FUNÇÕES DA PAGINA CLIENTES

def dados_cliente(request):
    # Exibir todos os clientes ja cadastrados em uma nova pagina
    todos_clientes = clientes.objects.all()
    
    lista = {
        'dados_cliente': todos_clientes
    }
    # Retorna os dados para a pagina de listagem de produtos
    return render(request, 'visual/clientes.html', lista)    

def add_cliente(request):
    if request.method == 'POST':
        form = Cliente_Form(request.POST)

        if form.is_valid():
            novo_cliente = form.save(commit=False)
            novo_cliente.done = 'doing'
            novo_cliente.save()
            return redirect('/clientes')

    else:
        form = Cliente_Form()
        return render(request,'visual/add_cliente.html', {'form': form})
    
def edit_cliente(request, id):
    cliente_edit = get_object_or_404(clientes, id_cliente=id)
    form = Cliente_Form(instance=cliente_edit)

    if(request.method == 'POST'):
        form = Cliente_Form(request.POST, instance=cliente_edit)

        if(form.is_valid()):
            cliente_edit.save()
            return redirect('/clientes')
        else:
            return render(request, 'visual/edit_cliente.html', {'form':form, 'cliente_edit': cliente_edit})
    else:
        return render(request, 'visual/edit_cliente.html', {'form':form, 'cliente_edit': cliente_edit})
    
def delete_cliente(request, id):
    cliente = get_object_or_404(clientes, id_cliente=id)
    cliente.delete()
    messages.success(request, 'Cliente deletado com sucesso!')
    return redirect('/clientes')


# FUNÇÕES DA PAGINA CAIXA

def caixa(request):
    todos_clientes = clientes.objects.all()
    
    lista = {
        'dados_cliente': todos_clientes
    }
    
    return render(request, 'visual/caixa.html', lista)
    

def caixa_cliente(request, id):
    estoque = produtos.objects.all()

    cliente = get_object_or_404(clientes,id_cliente=id)

    # Itens da cesta (temporária)
    cesta = Cesta.objects.filter(cliente=cliente)

    total_cesta = cesta.aggregate(total=Sum('subtotal'))['total'] or 0

    contexto = {
        'estoque': estoque,
        'cesta': cesta,
        'total_cesta': total_cesta,
        'cliente_id': id,
        'cliente': cliente
    }

    return render(request, 'visual/caixa_cliente.html', contexto)

def adicionar_item(request, cliente_id, produto_id):
    if request.method == 'POST':
        cliente = get_object_or_404(clientes, id_cliente=cliente_id)
        produto = get_object_or_404(produtos, id=produto_id)
        
        try:
            quant = int(request.POST.get('quantidade', 1))
            if quant <= 0:
                return redirect('caixa_cliente', id=cliente_id)
            
            preco_unit = produto.preco
            subtotal = quant * preco_unit
            
            # Verifica se o item já está na cesta
            item, criado = Cesta.objects.get_or_create(
                cliente=cliente,
                produto=produto,
                defaults={
                    'quantidade': quant,
                    'preco_unit': produto.preco,
                    'subtotal': subtotal
                }
            )

            if not criado:
                # Atualiza quantidade e subtotal
                item.quantidade += quant
                item.subtotal = item.quantidade * item.preco_unit
                item.save()

        except Exception as e:
            print("Erro ao adicionar item:", e)

    return redirect('caixa_cliente', id=cliente_id)

def remover_item(request, item_id):
    if request.method == 'POST':
        try:
            item = get_object_or_404(Cesta, id=item_id)
            cliente_id = item.cliente.id_cliente

            quant = int(request.POST.get('quantidade', 1))
            if quant <= 0:
                return redirect('caixa_cliente', id=cliente_id)

            # Remove parcialmente ou completamente
            if quant >= item.quantidade:
                item.delete()
            else:
                item.quantidade -= quant
                item.subtotal = item.quantidade * item.preco_unit
                item.save()

        except Exception as e:
            print("Erro ao remover item:", e)
            return redirect('caixa_cliente', id=item.cliente.id_cliente)

        return redirect('caixa_cliente', id=cliente_id)

def fechar_conta(request):
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente_id')
            forma_pag = int(request.POST.get('forma_pag'))
            valor_pag = Decimal(request.POST.get('valor_pag').replace(',','.'))
            desconto = Decimal(request.POST.get('desconto', '0'))
            desconto_decimal = (Decimal('100') - desconto) / Decimal('100')

            cliente = get_object_or_404(clientes, id_cliente=cliente_id)
            itens = Cesta.objects.filter(cliente=cliente)

            if not itens.exists():
                return redirect('caixa_cliente', id=cliente_id)

            total_bruto = sum(item.quantidade * item.preco_unit for item in itens)
            total_com_desconto = total_bruto * desconto_decimal

            if valor_pag < total_com_desconto:
                messages.warning(request, 'Valor pago insuficiente.')
                return redirect('caixa_cliente', id=cliente_id)

            troco = valor_pag - total_com_desconto

            # Criar registro de venda
            venda = vendas.objects.create(
                id_cliente=cliente,
                valor_total=total_com_desconto,
                desconto=desconto,  # ou use algum campo/formulário
                data_hora=timezone.now()
            )

            # Criar itens da venda
            for item in itens:
                itens_venda.objects.create(
                    id_vendas=venda,
                    prod_id=item.produto,
                    quantidade=item.quantidade,
                    preco_unit=item.preco_unit,
                    subtotal=item.quantidade * item.preco_unit
                )

                # Atualizar o estoque
                produto = item.produto
                produto.quantidade -= item.quantidade
                produto.save()

            pagamentos.objects.create(
                id_vendas=venda,
                forma_pag=forma_pag,
                valor_pag=valor_pag,
                troco=troco
            )


            # Limpar a cesta
            itens.delete()
            messages.success(request, 'Conta fechada com sucesso!')
            return redirect('caixa_cliente', id=cliente_id)
        
        except Exception as e:
            print("Erro ao fechar conta:", e)
            messages.error(request, 'Erro ao finalizar conta.')
            return redirect('caixa_cliente', id=cliente_id)