#!/usr/bin/env python
"""
Script para crear usuarios de prueba para testing de funcionalidades de spaces
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def create_test_users():
    """Crear usuarios de prueba"""

    test_users = [
        {
            'username': 'maria_test',
            'email': 'maria@test.com',
            'first_name': 'María',
            'last_name': 'García',
            'password': 'testpass123'
        },
        {
            'username': 'carlos_test',
            'email': 'carlos@test.com',
            'first_name': 'Carlos',
            'last_name': 'López',
            'password': 'testpass123'
        },
        {
            'username': 'ana_test',
            'email': 'ana@test.com',
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'password': 'testpass123'
        },
        {
            'username': 'luis_test',
            'email': 'luis@test.com',
            'first_name': 'Luis',
            'last_name': 'Rodríguez',
            'password': 'testpass123'
        }
    ]

    created_users = []

    for user_data in test_users:
        # Check if user already exists
        if User.objects.filter(username=user_data['username']).exists():
            print(f"❌ Usuario {user_data['username']} ya existe")
            continue

        # Create user
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            password=user_data['password']
        )

        created_users.append(user)
        print(f"✅ Usuario creado: {user.first_name} {user.last_name} ({user.username})")

    print(f"\n🎉 {len(created_users)} usuarios de prueba creados exitosamente!")
    print("\n📋 **Instrucciones para probar:**")
    print("1. Ve a tu espacio existente")
    print("2. Copia el código de invitación")
    print("3. Abre una ventana de incógnito")
    print("4. Regístrate/inicia sesión con uno de estos usuarios:")

    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            continue
        print(f"   - Usuario: {user_data['username']} | Contraseña: {user_data['password']}")

    print("5. Únete al espacio usando el código de invitación")
    print("6. Repite para agregar más miembros")
    print("7. Luego regresa a tu cuenta principal para probar la gestión de miembros")

if __name__ == '__main__':
    create_test_users()