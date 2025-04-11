from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe


def redirect_to_recipe(request, pk):
    """Функция перенаправляет запрос с короткого адреса на основной"""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'Рецепта с pk={pk} не существует')
    return redirect(f'/recipes/{pk}/')
