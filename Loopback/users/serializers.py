
from rest_framework import serializers
from .models import User
from profiles.models import MentorProfile, MenteeProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import RegisterSerializer
import requests
from django.core.files.base import ContentFile
from urllib.parse import urlparse
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.account.utils import user_email
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.serializers import LoginSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer


User = get_user_model()

def download_image_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = urlparse(url).path.split('/')[-1] or 'image.jpg'
            return ContentFile(response.content, name=filename)
    except Exception:
        pass
    return None

# This serialiszer is used to manage role-based access control and attributes based control to profile models from user registration.
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    # Support both file and URL
    passport_image = serializers.ImageField(required=False, allow_null=True)
    passport_image_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    # Extended profile fields
    company = serializers.CharField(required=False, allow_blank=True)
    job_title = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    interests = serializers.CharField(required=False, allow_blank=True)
    goals = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, allow_null=True)
    linkedin = serializers.URLField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    X_account = serializers.CharField(required=False, allow_blank=True)
    expertise = serializers.CharField(required=False, allow_blank=True)
    is_available = serializers.BooleanField(required=False)
    address = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    google_credentials = serializers.JSONField(required=False, allow_null=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'role',
            'passport_image', 'passport_image_url', 'company', 'job_title', 'industry', 'bio',
            'interests', 'goals', 'skills', 'experience_years', 'linkedin',
            'website', 'X_account', 'expertise', 'is_available', 'address',
            'phone_number', 'state', 'country', 'google_credentials', 'username'
        ]

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')

        passport_image = validated_data.pop('passport_image', None)
        passport_image_url = validated_data.pop('passport_image_url', None)

        # Use uploaded file first, fallback to image URL
        if not passport_image and passport_image_url:
            passport_image = download_image_from_url(passport_image_url)

        # Extract shared profile fields
        profile_fields = {
            'passport_image': validated_data.pop('passport_image', None),
            'first_name': validated_data.get('first_name'),
            'last_name': validated_data.get('last_name'),
            'company': validated_data.pop('company', ''),
            'job_title': validated_data.pop('job_title', ''),
            'industry': validated_data.pop('industry', ''),
            'bio': validated_data.pop('bio', ''),
            'interests': validated_data.pop('interests', ''),
            'goals': validated_data.pop('goals', ''),
            'skills': validated_data.pop('skills', ''),
            'experience_years': validated_data.pop('experience_years', 0),
            'linkedin': validated_data.pop('linkedin', ''),
            'website': validated_data.pop('website', ''),
            'X_account': validated_data.pop('X_account', ''),
            'expertise': validated_data.pop('expertise', ''),
            'is_available': validated_data.pop('is_available', True),
            'address': validated_data.pop('address', ''),
            'phone_number': validated_data.pop('phone_number', ''),
            'state': validated_data.pop('state', ''),
            'country': validated_data.pop('country', ''),
            'google_credentials': validated_data.pop('google_credentials', None),
            'username': validated_data.pop('username', '')

        }

        # Create the user
        user = User.objects.create_user(
            password=password,
            role=role,
            **validated_data
        )
        user.is_active = False
        user.save()

        # update the profile
        if role == 'mentor':
            profile, _ = MentorProfile.objects.get_or_create(user=user)
        elif role == 'mentee':
            profile, _ = MenteeProfile.objects.get_or_create(user=user)

        for field, value in profile_fields.items():
            setattr(profile, field, value)
        profile.save()

        return user




# GOOGLE OAUTH2 REGISTRATION/LOGIN SERIALIZER
class CustomRegisterSerializer(RegisterSerializer):
    username = None  # remove username field

    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        }



class CustomLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user  # The authenticated user object

        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'verified': user.verified,
        }

        return data

class CustomSocialLoginSerializer(SocialLoginSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)

        email = user_email(attrs['user'])

        try:
            # Check for existing user with same email
            existing_user = User.objects.get(email=email)

            # Only override if no social account exists yet for this user
            if not SocialAccount.objects.filter(user=existing_user, provider='google').exists():
                attrs['user'] = existing_user

        except User.DoesNotExist:
            pass

        return attrs


# AUTHENTICATION SERIALIZER FOR LOGIN API
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.verified:
            raise serializers.ValidationError('Please verify your email before logging in.')
        data['user_id'] = self.user.id
        data['role'] = self.user.role
        return data


# class CustomTokenRefreshSerializer(TokenRefreshSerializer):
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         # Here, only access is returned by default. Do not include refresh again.
#         return {
#             'access': data['access'],
#         }