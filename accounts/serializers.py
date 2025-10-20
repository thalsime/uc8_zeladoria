from rest_framework import serializers
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import Token
from .models import Profile
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from core.serializers import RelativeImageField


class ProfileSerializer(serializers.ModelSerializer):
    """Serializa dados do modelo Profile de um usuário."""
    nome = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    profile_picture = RelativeImageField(required=False, allow_null=True)


    class Meta:
        model = Profile
        fields = ['nome', 'profile_picture']

    def update(self, instance, validated_data):
        """Atualiza a instância do perfil e o nome do usuário associado."""
        user_data = validated_data.pop('user', {})
        nome = user_data.get('first_name')

        if nome is not None:
            instance.user.first_name = nome
            instance.user.save()

        # Explicitamente trata a remoção da foto de perfil no PUT se não for enviada
        is_put = not self.partial # Verifica se é PUT (não parcial)
        profile_picture_in_data = 'profile_picture' in validated_data


        if is_put and not profile_picture_in_data:
            # Se for PUT e 'profile_picture' NÃO veio nos dados validados,
            # força a definição como None na instância ANTES do super().update()
            # Isso garante que o save() do modelo veja a intenção de limpar o campo.
            if instance.profile_picture: # Se realmente havia uma imagem antiga
                 instance.profile_picture.delete(save=False) # Tenta deletar o arquivo antigo explicitamente
            instance.profile_picture = None

        # Chama o update padrão, que agora funcionará corretamente
        # para os outros campos e para o profile_picture (se ele veio nos dados)
        instance = super().update(instance, validated_data)
        return instance

class NestedProfileSerializer(serializers.ModelSerializer):
    """Serializador simplificado do perfil para uso aninhado."""
    profile_picture = RelativeImageField(read_only=True)

    class Meta:
        model = Profile
        fields = ['profile_picture']

class UserSerializer(serializers.ModelSerializer):
    """Serializa os dados essenciais do modelo User para exibição."""
    nome = serializers.CharField(source='first_name', read_only=True)
    profile = NestedProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_superuser', 'groups', 'nome', 'profile']


class LoginSerializer(serializers.Serializer):
    """Valida as credenciais de um usuário e gera um token de autenticação."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)
    user_data = UserSerializer(read_only=True)

    def validate(self, data):
        """Verifica se as credenciais de usuário são válidas."""
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
    Serializador para a criação de novos usuários por administradores.
    Inclui validação de confirmação e força de senha.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    nome = serializers.CharField(source='first_name', required=False, allow_blank=True)
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        required=False
    )
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'confirm_password', 'email', 'is_superuser', 'groups', 'nome', 'profile')
        read_only_fields = ('profile',)

    def validate(self, attrs):
        """
        Valida os dados, garantindo que as senhas coincidam e
        executando os validadores de força de senha do Django.
        """
        if attrs['password'] != attrs['confirm_password']:
            # Levanta como lista para consistência com validate_password
            raise serializers.ValidationError({"password": ["As senhas não coincidem."]})

        user_temp = User(
            username=attrs.get('username'),
            email=attrs.get('email'),
            first_name=attrs.get('nome', '') # 'nome' é source='first_name'
        )

        try:
            validate_password(password=attrs['password'], user=user_temp)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})

        return attrs

    def create(self, validated_data):
        """
        Cria o objeto User, define o nome e grupos, e retorna o usuário.
        """
        validated_data.pop('confirm_password')
        nome = validated_data.pop('first_name', None)
        groups_data = validated_data.pop('groups', [])

        # Cria o usuário (campos restantes: username, password, email, is_superuser)
        user = User.objects.create_user(**validated_data)

        # Define o nome, se fornecido
        if nome:
            user.first_name = nome
            user.save(update_fields=['first_name'])

        # Define os grupos, se fornecidos
        if groups_data:
            user.groups.set(groups_data)

        return user # Retorna apenas o objeto User (a view cuidará do token)

class PasswordChangeSerializer(serializers.Serializer):
    """Serializa os dados para a alteração de senha de um usuário autenticado."""
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        """Valida a senha antiga do usuário e a confirmação da nova senha."""
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "As novas senhas não coincidem."})

        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "A senha antiga está incorreta."})

        return data

    def validate_new_password(self, value):
        """Aplica os validadores de força de senha do Django à nova senha."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

class AdminPasswordChangeSerializer(serializers.Serializer):
    """Serializa dados para que um administrador altere a senha de um usuário."""
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        """Valida se a nova senha e a confirmação de senha são idênticas."""
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "As novas senhas não coincidem."})
        return data

    def validate_new_password(self, value):
        """Aplica os validadores de força de senha do Django à nova senha."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

class GroupSerializer(serializers.ModelSerializer):
    """Serializa os dados do modelo Group do Django."""
    class Meta:
        model = Group
        fields = ['id', 'name']
