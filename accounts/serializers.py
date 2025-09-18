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

        return super().update(instance, validated_data)

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
    """Serializa os dados para a criação de um novo usuário."""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    nome = serializers.CharField(source='first_name', required=False, allow_blank=True)
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False,
        help_text="Lista de IDs de grupos aos quais o usuário pertencerá."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'is_superuser', 'groups', 'nome']
        extra_kwargs = {
            'is_superuser': {'required': False, 'default': False},
            'email': {'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        """Valida se a senha e a confirmação de senha são idênticas."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return data

    def validate_password(self, value):
        """Aplica os validadores de força de senha do Django."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        """Cria e retorna uma nova instância de User com os dados validados."""
        groups_data = validated_data.pop('groups', None)
        validated_data.pop('confirm_password')

        user = User.objects.create_user(**validated_data)

        if groups_data:
            user.groups.set(groups_data)

        Token.objects.get_or_create(user=user)
        return user


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