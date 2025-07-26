from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import produtos, clientes
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

    if(request.method == 'POST'):
        form = Prod_Form(request.POST, instance=prod_edit)

        if(form.is_valid()):
            prod_edit.save()
            return redirect('/estoque')
        else:
            return render(request, 'visual/edit_prod.html', {'form':form, 'prod_edit': prod_edit})
    else:
        return render(request, 'visual/edit_prod.html', {'form':form, 'prod_edit': prod_edit})


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
    cliente = get_object_or_404(clientes, id_cliente=id)
    todos_produtos = produtos.objects.all()
    
    
    lista = {
        'estoque': todos_produtos
    }
    

    return render(request, 'visual/caixa_cliente.html', {'lista':lista, 'cliente_edit': cliente})

@csrf_exempt
def atualizar_estoque(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            produto_id = data.get("id_produto")
            quantidade = int(data.get("quantidade"))

            produto = produtos.objects.get(id=produto_id)

            novo_estoque = produto.quantidade - quantidade  # subtrai mesmo com valor negativo

            if novo_estoque < 0:
                return JsonResponse({
                    "status": "erro",
                    "mensagem": "Estoque não pode ficar negativo."
                }, status=400)

            produto.quantidade = novo_estoque
            produto.save()

            return JsonResponse({"status": "ok"})

        except produtos.DoesNotExist:
            return JsonResponse({"status": "erro", "mensagem": "Produto não encontrado"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "erro", "mensagem": str(e)}, status=500)

    return JsonResponse({"status": "erro", "mensagem": "Método não permitido"}, status=405)