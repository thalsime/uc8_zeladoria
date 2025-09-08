"""
Módulo de Serializers para a aplicação Accounts.

Define como os dados relacionados a usuários (login, criação de usuário,
e mudança de senha) são serializados e deserializados para/de representações JSON.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para exibir detalhes básicos do modelo User do Django.

    Utilizado para retornar informações do usuário logado ou recém-criado,
    evitando exposição de senhas.

    :ivar id: :class:`int` ID único do usuário.
    :ivar username: :class:`str` Nome de usuário.
    :ivar email: :class:`str` Endereço de e-mail do usuário.
    :ivar is_staff: :class:`bool` Indica se o usuário pode acessar o painel de administração.
    :ivar is_superuser: :class:`bool` Indica se o usuário possui todas as permissões sem ser explicitamente atribuídas.
    """
    class Meta:
        """
        Metadados para o UserSerializer.
        """
        model = User
        fields = ['id', 'username', 'email', 'is_superuser']

class LoginSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de login.

    Processa as credenciais de login e retorna o token de autenticação
    junto com os dados básicos do usuário autenticado.

    :ivar username: :class:`str` Nome de usuário para login.
    :ivar password: :class:`str` Senha do usuário (apenas escrita, não retornada).
    :ivar token: :class:`str` Token de autenticação do usuário (apenas leitura).
    :ivar user_data: :class:`~accounts.serializers.UserSerializer` Dados básicos do usuário autenticado (apenas leitura).
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)
    user_data = UserSerializer(read_only=True)

    def validate(self, data: dict) -> dict:
        """
        Valida as credenciais de login fornecidas.

        Gera um token de autenticação para o usuário se as credenciais forem válidas.

        :param data: :class:`dict` Dicionário contendo 'username' e 'password'.
        :raises rest_framework.serializers.ValidationError: Se as credenciais forem inválidas ou campos obrigatórios estiverem ausentes.
        :returns: Os dados validados, incluindo o token e os dados do usuário.
        :rtype: dict
        """
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = User.objects.filter(username=username).first()
            if user and user.check_password(password):
                token, created = Token.objects.get_or_create(user=user)
                data['token'] = token.key
                data['user_data'] = UserSerializer(user).data
            else:
                raise serializers.ValidationError("Credenciais inválidas.")
        else:
            raise serializers.ValidationError("Usuário e senha são obrigatórios.")
        return data

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para a criação de novos usuários por um administrador.

    Requer confirmação de senha e permite definir privilégios de staff/superuser.

    :ivar password: :class:`str` Senha do novo usuário (apenas escrita).
    :ivar confirm_password: :class:`str` Confirmação da senha (apenas escrita).
    :ivar username: :class:`str` Nome de usuário do novo usuário.
    :ivar email: :class:`str` Endereço de e-mail do novo usuário.
    :ivar is_staff: :class:`bool` Indica se o novo usuário terá acesso ao painel de administração.
    :ivar is_superuser: :class:`bool` Indica se o novo usuário terá permissões de superusuário.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        """
        Metadados para o UserCreateSerializer.
        """
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'is_superuser']
        extra_kwargs = {
            'is_superuser': {'required': False, 'default': False},
            'email': {'required': False, 'allow_blank': True}
        }

    def validate(self, data: dict) -> dict:
        """
        Valida se os campos 'password' e 'confirm_password' coincidem.

        :param data: :class:`dict` Dicionário contendo os dados do usuário a ser criado.
        :raises rest_framework.serializers.ValidationError: Se as senhas não coincidirem.
        :returns: Os dados validados.
        :rtype: dict
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return data

    def create(self, validated_data: dict) -> User:
        """
        Cria uma nova instância do modelo User com os dados validados.

        Define a senha de forma segura e cria um token de autenticação para o novo usuário.

        :param validated_data: :class:`dict` Dicionário com os dados validados para criar o usuário.
        :returns: A nova instância de usuário criada.
        :rtype: :class:`~django.contrib.auth.models.User`
        """
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        Token.objects.get_or_create(user=user)

        return user

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer para mudança de senha de um usuário autenticado.

    Requer a senha antiga para validação e a nova senha com confirmação.

    :ivar old_password: :class:`str` A senha atual do usuário.
    :ivar new_password: :class:`str` A nova senha desejada.
    :ivar confirm_new_password: :class:`str` Confirmação da nova senha.
    """
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data: dict) -> dict:
        """
        Valida as senhas fornecidas e a senha antiga do usuário.

        :param data: :class:`dict` Dicionário contendo 'old_password', 'new_password' e 'confirm_new_password'.
        :raises rest_framework.serializers.ValidationError: Se as senhas não coincidirem ou a senha antiga estiver incorreta.
        :returns: Os dados validados.
        :rtype: dict
        """
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "As novas senhas não coincidem."})

        # A instância do usuário (self.instance) será definida na view
        # quando o serializer for instanciado com `serializer = PasswordChangeSerializer(data=request.data, instance=request.user)`
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "A senha antiga está incorreta."})

        return data

class AdminPasswordChangeSerializer(serializers.Serializer):
    """
    Serializer para administradores alterarem a senha de qualquer usuário.

    Não requer a senha antiga, apenas a nova senha com confirmação.

    :ivar new_password: :class:`str` A nova senha desejada para o usuário.
    :ivar confirm_new_password: :class:`str` Confirmação da nova senha.
    """
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data: dict) -> dict:
        """
        Valida se as novas senhas fornecidas coincidem.

        :param data: :class:`dict` Dicionário contendo 'new_password' e 'confirm_new_password'.
        :raises rest_framework.serializers.ValidationError: Se as novas senhas não coincidem.
        :returns: Os dados validados.
        :rtype: dict
        """
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "As novas senhas não coincidem."})
        return data