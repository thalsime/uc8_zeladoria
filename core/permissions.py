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


class IsSolicitanteServicosUser(permissions.BasePermission):
    """
    Permite o acesso apenas a usuários que pertencem ao grupo 'Solicitante de Serviços'.
    """
    def has_permission(self, request, view):
        """Verifica se o usuário da requisição pertence ao grupo 'Solicitante de Serviços'."""
        return _is_in_group(request.user, 'Solicitante de Serviços')


class IsAdminOrZeladoria(permissions.BasePermission):
    """
    Permissão customizada para permitir acesso a administradores ou a usuários
    que pertençam ao grupo 'Zeladoria'.

    Esta classe encapsula uma regra de negócio específica onde certos recursos
    são acessíveis por múltiplos perfis, garantindo que a lógica de permissão
    seja centralizada e reutilizável, em conformidade com o princípio DRY.
    """

    def has_permission(self, request, view):
        """
        Verifica se o usuário solicitante tem permissão para acessar o recurso.

        A permissão é concedida se o usuário estiver autenticado E for um superusuário
        OU for membro do grupo 'Zeladoria'.

        Args:
            request: O objeto da requisição HTTP, contendo os dados do usuário.
            view: A view da API que está sendo acessada.

        Returns:
            True se o usuário for um superusuário ou pertencer ao grupo 'Zeladoria',
            False caso contrário.
        """
        user = request.user
        return (
            user and
            user.is_authenticated and
            (user.is_superuser or user.groups.filter(name='Zeladoria').exists())
        )
