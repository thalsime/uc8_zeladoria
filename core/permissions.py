"""
Módulo de Permissões Personalizadas para o DRF.

Define um conjunto de classes de permissão reutilizáveis para controlar o acesso
a diferentes partes da API com base nos papéis e grupos dos usuários.
"""

from rest_framework import permissions

def _is_in_group(user, group_name):
    """
    Verifica se um usuário pertence a um grupo específico.

    :param user: A instância do usuário a ser verificada.
    :type user: :class:`~django.contrib.auth.models.User`
    :param group_name: O nome do grupo a ser verificado.
    :type group_name: str
    :returns: True se o usuário pertencer ao grupo, False caso contrário.
    :rtype: bool
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


class IsAdminUser(permissions.BasePermission):
    """
    Permissão personalizada para permitir acesso apenas a usuários administradores.

    Um administrador é definido como um usuário que tem o atributo `is_staff` como True.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsZeladorUser(permissions.BasePermission):
    """
    Permissão personalizada para permitir acesso apenas a usuários do grupo 'Zeladoria'.
    """
    def has_permission(self, request, view):
        return _is_in_group(request.user, 'Zeladoria')


class IsCorpoDocenteUser(permissions.BasePermission):
    """
    Permissão personalizada para permitir acesso apenas a usuários do grupo 'Corpo Docente'.
    """
    def has_permission(self, request, view):
        return _is_in_group(request.user, 'Corpo Docente')