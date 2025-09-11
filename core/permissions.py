from rest_framework import permissions


def _is_in_group(user, group_name):
    """Verifica se um usuário pertence a um grupo com o nome especificado.

    É uma função auxiliar para as classes de permissão baseadas em grupo.

    Args:
        user (User): A instância de usuário a ser verificada.
        group_name (str): O nome do grupo a ser verificado.

    Returns:
        bool: True se o usuário pertencer ao grupo, False caso contrário.
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


class IsAdminUser(permissions.BasePermission):
    """Permite o acesso apenas a usuários com privilégios de superusuário.

    Esta permissão verifica se o atributo `is_superuser` do usuário é `True`.
    """
    def has_permission(self, request, view):
        """Verifica se o usuário da requisição é um superusuário autenticado."""
        return request.user and request.user.is_superuser


class IsZeladorUser(permissions.BasePermission):
    """Permite o acesso apenas a usuários que pertencem ao grupo 'Zeladoria'."""
    def has_permission(self, request, view):
        """Verifica se o usuário da requisição pertence ao grupo 'Zeladoria'."""
        return _is_in_group(request.user, 'Zeladoria')


class IsCorpoDocenteUser(permissions.BasePermission):
    """Permite o acesso apenas a usuários que pertencem ao grupo 'Corpo Docente'."""
    def has_permission(self, request, view):
        """Verifica se o usuário da requisição pertence ao grupo 'Corpo Docente'."""
        return _is_in_group(request.user, 'Corpo Docente')