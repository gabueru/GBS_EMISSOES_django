from django import forms
from .models import produtos, clientes

class Prod_Form(forms.ModelForm):

    class Meta:
        model = produtos
        fields = ('tipo', 'nome', 'preco', 'medida', 'quantidade')

class Cliente_Form(forms.ModelForm):

    class Meta:
        model = clientes
        fields = ('nome_cliente', 'contato')