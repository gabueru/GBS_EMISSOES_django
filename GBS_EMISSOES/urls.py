from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # login page
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Home page
    path('', views.home, name='home'),


    # Clientes page
    path('clientes/', views.dados_cliente, name='clientes'),
    # add client
    path('clientes/add', views.add_cliente, name='add_cliente'),
    # edit client
    path('clientes/edit/<int:id>/', views.edit_cliente, name='edit_cliente'),
    # delete client
    path('clientes/delete/<int:id>/', views.delete_cliente, name='delete_cliente'),


    # Caixa page
    path('caixa/', views.caixa, name='caixa'),
    # Conta do cliente
    path('caixa/<int:id>', views.caixa_cliente, name='caixa_cliente'),
    # Adicionar item na cesta
    path('caixa/<int:cliente_id>/add/<int:produto_id>/', views.adicionar_item, name='adicionar_item'),
    # Remover item da cexta
    path('remover-item/<int:item_id>/', views.remover_item, name='remover_item'),
    # Fechar conta
    path('fechar-conta/', views.fechar_conta, name='fechar_conta'),


    # Relatorios page
    path('relatorios/', views.relatorios, name='relatorios'),
    # html do recibo
    path('recibo/<int:venda_id>/', views.gerar_recibo, name='gerar_recibo'),




    # Estoque page
    path('estoque/', views.estoque, name='estoque'),
    # add product
    path('estoque/add/', views.add_produto, name='add_produto'),
    # delete product
    path('estoque/delete/<int:id>/', views.delete_produto, name='delete_produto'),
    # edit product
    path('estoque/edit/<int:id>/', views.edit_produto, name='edit_produto'),

]
