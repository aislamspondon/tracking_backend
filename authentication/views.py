# from django.shortcuts import render
from authentication.serializers import UserSerializerWithToken
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# Create your views here.
User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerWithToken(self.user).data
        for key, value in serializer.items():
            data[key] = value
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['GET'])
def intro(request):
    return Response(data={"message": "Hello Auth"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def registerUser(request):
    data = request.data
    user = User.objects.create(
        first_name = data['first_name'],
        last_name = data['last_name'],
        username = data['username'], 
        email = data['email'], 
        phone_number = data['phone_number'],
        password = make_password(data['password'])
    )
    serializer = UserSerializerWithToken(user)
    
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteUser(request, pk):
    userForDeletion = User.objects.get(id=pk)
    userForDeletion.delete()
    return Response('User was deleted')

