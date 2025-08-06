from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.utils import timezone
from decimal import Decimal
from .models import produtos, clientes, Cesta, vendas, itens_venda, pagamentos
from .forms import Prod_Form, Cliente_Form
from django import forms
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from django.utils.dateparse import parse_date
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# =================== AUTENTICAÇÃO ===================
def cadastro_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        if User.objects.filter(username=usuario).exists():
            messages.error(request, 'Usuário já existe.')
            return redirect('cadastro')

        user = User.objects.create_user(username=usuario, email=email, password=senha)
        user.save()
        messages.success(request, 'Cadastro realizado com sucesso. Faça login!')
        return redirect('login')

    return render(request, 'visual/cadastro.html')

def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')

        user = authenticate(request, username=usuario, password=senha)

        if user is not None:
            login(request, user)
            return redirect('home') 
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
            return redirect('login')

    return render(request, 'visual/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    return render(request, 'visual/home.html')

# =================== RELATÓRIOS ===================
@login_required
def relatorios(request):
    vendas_filtradas = vendas.objects.select_related('id_cliente').filter(usuario=request.user)

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    cliente_nome = request.GET.get('cliente')

    if data_inicio:
        vendas_filtradas = vendas_filtradas.filter(data_hora__date__gte=parse_date(data_inicio))
    if data_fim:
        vendas_filtradas = vendas_filtradas.filter(data_hora__date__lte=parse_date(data_fim))
    if cliente_nome:
        vendas_filtradas = vendas_filtradas.filter(id_cliente__nome_cliente__icontains=cliente_nome)

    vendas_filtradas = vendas_filtradas.order_by('-data_hora')

    return render(request, 'visual/relatorios.html', {
        'vendas': vendas_filtradas
    })

@login_required
def gerar_relatorio_pdf(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    cliente_nome = request.GET.get('cliente')

    vendas_filtradas = vendas.objects.select_related('id_cliente').all()

    if data_inicio:
        vendas_filtradas = vendas_filtradas.filter(data_hora__date__gte=parse_date(data_inicio))
    if data_fim:
        vendas_filtradas = vendas_filtradas.filter(data_hora__date__lte=parse_date(data_fim))
    if cliente_nome:
        vendas_filtradas = vendas_filtradas.filter(id_cliente__nome_cliente__icontains=cliente_nome)

    # Calcula o total
    total_geral = vendas_filtradas.aggregate(total=Sum('valor_total'))['total'] or 0

    html_string = render_to_string('visual/relatorio_pdf.html', {
        'vendas': vendas_filtradas,
        'total_geral': total_geral,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=relatorio_vendas.pdf'
    weasyprint.HTML(string=html_string).write_pdf(response)

    return response

@login_required
def gerar_recibo(request, venda_id):
    venda = get_object_or_404(vendas, id=venda_id, usuario=request.user)
    itens = itens_venda.objects.filter(id_vendas=venda)
    pagamento = pagamentos.objects.filter(id_vendas=venda).first()

    html_string = render_to_string('visual/recibo_pdf.html', {
        'venda': venda,
        'itens': itens,
        'pagamento': pagamento
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=recibo_venda_{venda_id}.pdf'
    weasyprint.HTML(string=html_string).write_pdf(response)
    return response

# =================== ESTOQUE ===================
@login_required
def estoque(request):
    todos_produtos = produtos.objects.filter(usuario=request.user)
    return render(request, 'visual/estoque.html', {'estoque': todos_produtos})

@login_required
def add_produto(request):
    if request.method == 'POST':
        form = Prod_Form(request.POST)
        if form.is_valid():
            novo_prod = form.save(commit=False)
            novo_prod.usuario = request.user
            novo_prod.save()
            return redirect('/estoque')
    else:
        form = Prod_Form()
    return render(request, 'visual/add_prod.html', {'form': form})

@login_required
def delete_produto(request, id):
    produto = get_object_or_404(produtos, id=id, usuario=request.user)
    produto.delete()
    messages.success(request, 'Produto deletado com sucesso!')
    return redirect('/estoque')

@login_required
def edit_produto(request, id):
    prod_edit = get_object_or_404(produtos, id=id, usuario=request.user)
    form = Prod_Form(instance=prod_edit)

    if request.method == 'POST':
        form = Prod_Form(request.POST, instance=prod_edit)
        if form.is_valid():
            prod_edit.save()
            return redirect('/estoque')
    return render(request, 'visual/edit_prod.html', {'form': form, 'prod_edit': prod_edit})

# =================== CLIENTES ===================
@login_required
def dados_cliente(request):
    todos_clientes = clientes.objects.filter(usuario=request.user)
    return render(request, 'visual/clientes.html', {'dados_cliente': todos_clientes})

@login_required
def add_cliente(request):
    if request.method == 'POST':
        form = Cliente_Form(request.POST)
        if form.is_valid():
            novo_cliente = form.save(commit=False)
            novo_cliente.usuario = request.user
            novo_cliente.save()
            return redirect('/clientes')
    else:
        form = Cliente_Form()
    return render(request, 'visual/add_cliente.html', {'form': form})

@login_required
def edit_cliente(request, id):
    cliente_edit = get_object_or_404(clientes, id_cliente=id, usuario=request.user)
    form = Cliente_Form(instance=cliente_edit)

    if request.method == 'POST':
        form = Cliente_Form(request.POST, instance=cliente_edit)
        if form.is_valid():
            cliente_edit.save()
            return redirect('/clientes')
    return render(request, 'visual/edit_cliente.html', {'form': form, 'cliente_edit': cliente_edit})

@login_required
def delete_cliente(request, id):
    cliente = get_object_or_404(clientes, id_cliente=id, usuario=request.user)
    cliente.delete()
    messages.success(request, 'Cliente deletado com sucesso!')
    return redirect('/clientes')

# =================== CAIXA ===================
@login_required
def caixa(request):
    todos_clientes = clientes.objects.filter(usuario=request.user)
    return render(request, 'visual/caixa.html', {'dados_cliente': todos_clientes})

@login_required
def caixa_cliente(request, id):
    cliente = get_object_or_404(clientes, id_cliente=id, usuario=request.user)
    estoque = produtos.objects.filter(usuario=request.user)
    cesta = Cesta.objects.filter(cliente=cliente, usuario=request.user)
    total_cesta = cesta.aggregate(total=Sum('subtotal'))['total'] or 0

    return render(request, 'visual/caixa_cliente.html', {
        'estoque': estoque,
        'cesta': cesta,
        'total_cesta': total_cesta,
        'cliente_id': id,
        'cliente': cliente
    })

@login_required
def adicionar_item(request, cliente_id, produto_id):
    if request.method == 'POST':
        cliente = get_object_or_404(clientes, id_cliente=cliente_id, usuario=request.user)
        produto = get_object_or_404(produtos, id=produto_id, usuario=request.user)
        try:
            quant = int(request.POST.get('quantidade', 1))
            if quant <= 0:
                return redirect('caixa_cliente', id=cliente_id)

            preco_unit = produto.preco
            subtotal = quant * preco_unit

            item, criado = Cesta.objects.get_or_create(
                cliente=cliente,
                produto=produto,
                usuario=request.user,
                defaults={
                    'quantidade': quant,
                    'preco_unit': produto.preco,
                    'subtotal': subtotal
                }
            )

            if not criado:
                item.quantidade += quant
                item.subtotal = item.quantidade * item.preco_unit
                item.save()

        except Exception as e:
            print("Erro ao adicionar item:", e)

    return redirect('caixa_cliente', id=cliente_id)

@login_required
def remover_item(request, item_id):
    if request.method == 'POST':
        try:
            item = get_object_or_404(Cesta, id=item_id, usuario=request.user)
            cliente_id = item.cliente.id_cliente
            quant = int(request.POST.get('quantidade', 1))

            if quant <= 0:
                return redirect('caixa_cliente', id=cliente_id)

            if quant >= item.quantidade:
                item.delete()
            else:
                item.quantidade -= quant
                item.subtotal = item.quantidade * item.preco_unit
                item.save()

        except Exception as e:
            print("Erro ao remover item:", e)

        return redirect('caixa_cliente', id=cliente_id)

@login_required
def fechar_conta(request):
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente_id')
            forma_pag = int(request.POST.get('forma_pag'))
            valor_pag = Decimal(request.POST.get('valor_pag').replace(',', '.'))
            desconto = Decimal(request.POST.get('desconto', '0'))
            desconto_decimal = (Decimal('100') - desconto) / Decimal('100')

            cliente = get_object_or_404(clientes, id_cliente=cliente_id, usuario=request.user)
            itens = Cesta.objects.filter(cliente=cliente, usuario=request.user)

            if not itens.exists():
                return redirect('caixa_cliente', id=cliente_id)

            total_bruto = sum(item.quantidade * item.preco_unit for item in itens)
            total_com_desconto = total_bruto * desconto_decimal

            if valor_pag < total_com_desconto:
                messages.warning(request, 'Valor pago insuficiente.')
                return redirect('caixa_cliente', id=cliente_id)

            troco = valor_pag - total_com_desconto

            venda = vendas.objects.create(
                id_cliente=cliente,
                valor_total=total_com_desconto,
                desconto=desconto,
                data_hora=timezone.now(),
                usuario=request.user
            )

            for item in itens:
                itens_venda.objects.create(
                    id_vendas=venda,
                    prod_id=item.produto,
                    quantidade=item.quantidade,
                    preco_unit=item.preco_unit,
                    subtotal=item.quantidade * item.preco_unit,
                    usuario=request.user
                )
                produto = item.produto
                produto.quantidade -= item.quantidade
                produto.save()

            pagamentos.objects.create(
                id_vendas=venda,
                forma_pag=forma_pag,
                valor_pag=valor_pag,
                troco=troco,
                usuario=request.user
            )

            itens.delete()
            messages.success(request, f'Conta fechada com sucesso! Troco: R$ {troco:.2f}')
            return redirect('caixa')

        except Exception as e:
            print("Erro ao fechar conta:", e)
            messages.error(request, 'Erro ao finalizar conta.')
            return redirect('caixa_cliente', id=cliente_id)
