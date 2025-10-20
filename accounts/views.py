from rest_framework import viewsets, status, permissions, generics, parsers
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import generics
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group, User
from .models import Profile
from .serializers import (UserSerializer, LoginSerializer, UserCreateSerializer,
                          PasswordChangeSerializer, GroupSerializer, ProfileSerializer)
from .filters import UserFilter


class AuthViewSet(viewsets.ViewSet):
    """Agrupa endpoints relacionados à autenticação e gerenciamento de contas.

    Fornece ações para login, consulta de dados do usuário logado, listagem,
    criação de usuários e gerenciamento de senhas e perfis.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Realiza a autenticação de um usuário com base em username e password.

        Se as credenciais forem válidas, retorna os dados do usuário e um
        token de acesso à API.

        Args:
            request (Request): O objeto da requisição HTTP contendo os dados.

        Returns:
            Response: Uma resposta com os dados do usuário e o token de acesso.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def current_user(self, request):
        """Retorna os dados serializados do usuário atualmente autenticado.

        Acessível apenas por usuários que já possuem um token de acesso válido.

        Args:
            request (Request): O objeto da requisição HTTP.

        Returns:
            Response: Uma resposta com os dados do usuário autenticado.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_users(self, request):
        """Lista todos os usuários do sistema com suporte a filtros.

        Permite a consulta da lista de usuários aplicando filtros dinâmicos,
        como `username`, `email`, etc. Acesso restrito a administradores.

        Args:
            request (Request): O objeto da requisição HTTP.

        Returns:
            Response: Uma resposta com a lista de usuários filtrados.
        """
        queryset = User.objects.all().order_by('username')
        filterset = UserFilter(request.query_params, queryset=queryset)
        serializer = UserSerializer(filterset.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def create_user(self, request):
        """
        Cria um novo usuário e retorna seus dados e um token de autenticação.
        Acessível apenas por administradores (is_staff ou is_superuser).
        """
        serializer = UserCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.create(user=user)
            serialized_user = UserSerializer(user, context={'request': request}).data
            return Response({
                "message": "Usuário criado com sucesso.",
                "user": serialized_user,
                'token': token.key # Acessa a chave do token que acabamos de criar
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Permite que o usuário autenticado altere sua própria senha.

        Requer a senha antiga para verificação. Após a alteração, o token
        de autenticação antigo é invalidado e um novo é gerado.

        Args:
            request (Request): O objeto da requisição HTTP.

        Returns:
            Response: Uma resposta com uma mensagem de sucesso.
        """
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        Token.objects.filter(user=user).delete()
        token, created = Token.objects.get_or_create(user=user)

        return Response({'message': 'Senha alterada com sucesso.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_groups(self, request):
        """Lista todos os grupos de permissão (roles) disponíveis no sistema.

        Útil para que aplicações cliente possam exibir opções de grupos ao
        criar ou editar usuários.

        Args:
            request (Request): O objeto da requisição HTTP.

        Returns:
            Response: Uma resposta com a lista de grupos disponíveis.
        """
        groups = Group.objects.all().order_by('name')
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated], parser_classes=[parsers.MultiPartParser, parsers.JSONParser])
    def profile(self, request):
        """Gerencia o perfil do usuário autenticado.

        Permite a recuperação (GET) e a atualização (PUT/PATCH) dos dados
        do perfil, incluindo o upload da foto de perfil via `multipart/form-data`.

        Args:
            request (Request): O objeto da requisição HTTP.

        Returns:
            Response: Uma resposta com os dados do perfil.
        """
        profile = request.user.profile

        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            partial = (request.method == 'PATCH')
            serializer = ProfileSerializer(profile, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
