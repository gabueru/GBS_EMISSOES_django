from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.utils import timezone
from django.utils.timezone import now
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
import json
from django.core.paginator import Paginator


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
    vendas_diarias = (
        itens_venda.objects.filter(usuario=request.user)
        .values("id_vendas__data_hora__date")
        .annotate(total=Sum("subtotal"))
        .order_by("id_vendas__data_hora__date")
    )

    labels_vendas = [str(v["id_vendas__data_hora__date"]) for v in vendas_diarias]
    data_vendas = [float(v["total"]) for v in vendas_diarias]

    estoque_baixo = (
        produtos.objects.filter(usuario=request.user, tipo=1, quantidade__lte=5)
        .order_by("quantidade")
    )

    labels_estoque = [p.nome for p in estoque_baixo]
    data_estoque = [p.quantidade for p in estoque_baixo]

    mais_vendidos = (
        itens_venda.objects.filter(usuario=request.user)
        .values("prod_id__nome")
        .annotate(total_vendido=Sum("quantidade"))
        .order_by("-total_vendido")[:5]  # top 5
    )

    labels_mais_vendidos = [item["prod_id__nome"] for item in mais_vendidos]
    data_mais_vendidos = [int(item["total_vendido"]) for item in mais_vendidos]

    produtos_estoque_baixo = (
        produtos.objects.filter(tipo=1)  # só mercadorias
        .order_by('quantidade')[:8]      # 8 com menor estoque
        .values_list('nome', 'quantidade')
    )

    context = {
        "produtos_estoque_baixo": produtos_estoque_baixo,
        "labels_vendas": labels_vendas,
        "data_vendas": data_vendas,
        "labels_estoque": labels_estoque,
        "data_estoque": data_estoque,
        "labels_mais_vendidos": json.dumps(labels_mais_vendidos),
        "data_mais_vendidos": json.dumps(data_mais_vendidos),
    }
    return render(request, "visual/home.html", context)

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

    paginator = Paginator(vendas_filtradas, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    page_range= range(page_obj.paginator.num_pages)

    querydict = request.GET.copy()
    if "page" in querydict:
        querydict.pop("page")

    contexto = {
        'vendas': vendas_filtradas,
        'page_range': page_range,
        'page_obj': page_obj,
        "querystring": querydict.urlencode()
    }

    return render(request, 'visual/relatorios.html', contexto)

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
    prod_filtrados = produtos.objects.filter(usuario=request.user)
    tipo = request.GET.get('tipo')
    nome = request.GET.get('nome')

    if tipo:
        prod_filtrados = prod_filtrados.filter(tipo=tipo)
    if nome:
        prod_filtrados = prod_filtrados.filter(nome__icontains=nome)

    prod_filtrados = prod_filtrados.order_by('nome')


    paginator = Paginator(prod_filtrados, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    page_range = range(1, page_obj.paginator.num_pages + 1)

    querydict = request.GET.copy()
    if "page" in querydict:
        querydict.pop("page")

    contexto = {
        'page_range': page_range,
        'page_obj': page_obj,
        'prod_filtrados': prod_filtrados,
        "querystring": querydict.urlencode(),
    }

    return render(request, 'visual/estoque.html', contexto)

@login_required
def add_produto(request):
    if request.method == 'POST':
        form = Prod_Form(request.POST)
        if form.is_valid():
            novo_prod = form.save(commit=False)
            novo_prod.usuario = request.user

            tipo = request.POST.get('tipo')
            if tipo in ['2', '3']:
                novo_prod.quantidade = 0

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
            
            if produto.tipo == 1 and produto.quantidade < quant:
                messages.error(request, 'Estoque insuficiente.')
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
                if produto.tipo == 1:
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
