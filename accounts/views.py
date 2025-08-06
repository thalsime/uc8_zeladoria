"""
Módulo de Views para a aplicação Accounts.

Define o ViewSet para operações de autenticação e gerenciamento de usuários.
"""

from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth.models import User
from .serializers import UserSerializer, LoginSerializer, UserCreateSerializer, \
                         PasswordChangeSerializer, AdminPasswordChangeSerializer

class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet para operações de autenticação e gerenciamento de usuários.

    Este ViewSet oferece funcionalidades para login, obtenção de dados do usuário
    autenticado, criação de novos usuários por administradores e mudança de senhas,
    assim como a redefinição de senha para outros usuários por parte de administradores.

    :ivar permission_classes: :class:`list` Lista de classes de permissão que controlam o acesso
                              padrão para as ações do ViewSet. Por padrão, exige autenticação.
                              As permissões podem ser sobrescritas por ação usando `@action`.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Endpoint para login de usuário e obtenção de token de autenticação.

        Aceita credenciais de usuário (username e password) e, se válidas,
        retorna um token de autenticação e os dados básicos do usuário.

        :param request: O objeto da requisição HTTP, contendo as credenciais de login.
        :type request: :class:`~rest_framework.request.Request`
        :raises rest_framework.serializers.ValidationError: Se as credenciais forem inválidas ou incompletas.
        :returns: Uma resposta HTTP 200 OK contendo o token do usuário e seus dados.
        :rtype: :class:`~rest_framework.response.Response`
        :payload { "username": "string", "password": "string" }: Corpo da requisição com o nome de usuário e senha.
        :payloadtype username: str
        :payloadtype password: str
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def current_user(self, request):
        """
        Endpoint para obter os dados do usuário atualmente autenticado.

        Retorna os detalhes do usuário logado, como ID, nome de usuário, e-mail e status.

        :param request: O objeto da requisição HTTP, contendo o usuário autenticado.
        :type request: :class:`~rest_framework.request.Request`
        :returns: Uma resposta HTTP 200 OK contendo os dados do usuário autenticado.
        :rtype: :class:`~rest_framework.response.Response`
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_users(self, request):
        """
        Endpoint para listar todos os usuários do sistema.

        Acesso restrito apenas a usuários com permissões de administrador.
        Retorna os dados de todos os usuários, utilizando o UserSerializer
        para evitar exposição de informações sensíveis como senhas e tokens.

        :param request: O objeto da requisição HTTP.
        :type request: :class:`~rest_framework.request.Request`
        :returns: Uma resposta HTTP 200 OK com a lista de todos os usuários.
        :rtype: :class:`~rest_framework.response.Response`
        """
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def create_user(self, request):
        """
        Endpoint para um administrador criar novos usuários no sistema.

        Permite que administradores criem novas contas de usuário, definindo
        nome de usuário, e-mail, senha e status de staff/superuser.

        :param request: O objeto da requisição HTTP, contendo os dados para criação do usuário.
        :type request: :class:`~rest_framework.request.Request`
        :raises rest_framework.serializers.ValidationError: Se os dados de criação forem inválidos (ex: senhas não coincidem, campos obrigatórios ausentes).
        :returns: Uma resposta HTTP 201 CREATED contendo uma mensagem de sucesso,
                  os dados do novo usuário e seu token de autenticação.
        :rtype: :class:`~rest_framework.response.Response`
        :payload { "username": "string", "email": "string", "password": "string", "confirm_password": "string", "is_staff": boolean, "is_superuser": boolean }: Corpo da requisição com os dados do novo usuário.
        :payloadtype username: str
        :payloadtype email: str
        :payloadtype password: str
        :payloadtype confirm_password: str
        :payloadtype is_staff: bool
        :payloadtype is_superuser: bool
        """
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'message': 'Usuário criado com sucesso.',
            'user': UserSerializer(user).data,
            'token': user.auth_token.key
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Endpoint para um usuário autenticado mudar sua própria senha.

        Requer que o usuário forneça sua senha antiga para validação,
        e então define uma nova senha com confirmação.

        :param request: O objeto da requisição HTTP, contendo as senhas para alteração.
        :type request: :class:`~rest_framework.request.Request`
        :raises rest_framework.serializers.ValidationError: Se as senhas não coincidirem ou a senha antiga estiver incorreta.
        :returns: Uma resposta HTTP 200 OK com uma mensagem de sucesso.
        :rtype: :class:`~rest_framework.response.Response`
        :payload { "old_password": "string", "new_password": "string", "confirm_new_password": "string" }: Corpo da requisição com as senhas.
        :payloadtype old_password: str
        :payloadtype new_password: str
        :payloadtype confirm_new_password: str
        """
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Opcional: Reautenticar o usuário ou revogar o token antigo para maior segurança.
        Token.objects.filter(user=user).delete() # Isso invalidaria o token atual
        token, created = Token.objects.get_or_create(user=user) # Cria um novo token

        return Response({'message': 'Senha alterada com sucesso.'}, status=status.HTTP_200_OK)

    # TODO: Refatorar set_user_password().
    # Há falhas relacionadas a esse endpoint que precisa ser revisadas.

    # @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    # def set_user_password(self, request, pk=None):
    #     """
    #     Endpoint para um administrador mudar a senha de um usuário específico.
    #
    #     Permite que um administrador defina uma nova senha para qualquer usuário
    #     no sistema, sem a necessidade da senha antiga do usuário alvo.
    #
    #     :param request: O objeto da requisição HTTP, contendo a nova senha e sua confirmação.
    #     :type request: :class:`~rest_framework.request.Request`
    #     :param pk: O ID da chave primária do usuário cuja senha será alterada.
    #     :type pk: int
    #     :raises django.contrib.auth.models.User.DoesNotExist: Se o usuário com o `pk` fornecido não for encontrado.
    #     :raises rest_framework.serializers.ValidationError: Se as novas senhas não coincidirem.
    #     :returns: Uma resposta HTTP 200 OK com uma mensagem de sucesso, ou 404 NOT FOUND se o usuário não existir.
    #     :rtype: :class:`~rest_framework.response.Response`
    #     :payload { "new_password": "string", "confirm_new_password": "string" }: Corpo da requisição com as novas senhas.
    #     :payloadtype new_password: str
    #     :payloadtype confirm_new_password: str
    #     """
    #     try:
    #         user = User.objects.get(pk=pk)
    #     except User.DoesNotExist:
    #         return Response({'detail': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    #
    #     serializer = AdminPasswordChangeSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     user.set_password(serializer.validated_data['new_password'])
    #     user.save()
    #
    #     # Opcional: Revogar tokens existentes do usuário alvo para forçar reautenticação
    #     # Token.objects.filter(user=user).delete()
    #
    #     return Response({'message': f'Senha do usuário {user.username} alterada com sucesso.'}, status=status.HTTP_200_OK)