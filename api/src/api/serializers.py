from django.contrib.auth.models import User, Group
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User

        # 1) uncomment for the demo
        fields = ('url', 'first_name', 'last_name', 'username', 'email', 'groups')

        # 2) remote this block
        #fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')
