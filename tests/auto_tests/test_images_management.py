#!/usr/bin/env python3
"""
Автотест для проверки загрузки и управления изображениями
Проверяет:
1. Загрузку изображений с валидацией
2. Оптимизацию изображений в WebP
3. Управление порядком изображений
4. Удаление изображений
5. Кэширование изображений
"""

import os
import sys
import json
import time
import requests
from PIL import Image
import io
import tempfile
import shutil

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def create_test_image(width=800, height=600, format='JPEG'):
    """Создать тестовое изображение в памяти"""
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes.getvalue()

def create_large_test_image():
    """Создать большое тестовое изображение (>2MB)"""
    # Создаем изображение 2000x2000 пикселей для превышения лимита
    img = Image.new('RGB', (2000, 2000), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_image_upload_validation():
    """Тест валидации загрузки изображений"""
    print("🧪 Тестирование валидации загрузки изображений...")
    
    base_url = "http://localhost:8000"
    
    # Тест 1: Загрузка корректного изображения
    print("  ✓ Тест загрузки корректного изображения")
    test_image = create_test_image()
    
    files = {'file': ('test.jpg', test_image, 'image/jpeg')}
    data = {'image_type': 'logo'}
    
    response = requests.post(f"{base_url}/cms/api/images/upload", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("    ✅ Корректное изображение загружено успешно")
            return result['image']['id']
        else:
            print(f"    ❌ Ошибка загрузки: {result.get('message')}")
            return None
    else:
        print(f"    ❌ HTTP ошибка: {response.status_code}")
        return None

def test_image_size_validation():
    """Тест валидации размера файла"""
    print("  ✓ Тест валидации размера файла")
    
    base_url = "http://localhost:8000"
    large_image = create_large_test_image()
    
    files = {'file': ('large.jpg', large_image, 'image/jpeg')}
    data = {'image_type': 'logo'}
    
    response = requests.post(f"{base_url}/cms/api/images/upload", files=files, data=data)
    
    if response.status_code == 400:
        result = response.json()
        if "слишком большой" in result.get('message', '').lower():
            print("    ✅ Валидация размера файла работает корректно")
            return True
        else:
            print(f"    ❌ Неожиданное сообщение об ошибке: {result.get('message')}")
            return False
    else:
        print(f"    ❌ Ожидалась ошибка 400, получен код: {response.status_code}")
        return False

def test_image_format_validation():
    """Тест валидации формата файла"""
    print("  ✓ Тест валидации формата файла")
    
    base_url = "http://localhost:8000"
    
    # Создаем текстовый файл вместо изображения
    text_content = b"This is not an image"
    
    files = {'file': ('test.txt', text_content, 'text/plain')}
    data = {'image_type': 'logo'}
    
    response = requests.post(f"{base_url}/cms/api/images/upload", files=files, data=data)
    
    if response.status_code == 400:
        result = response.json()
        if "не является валидным изображением" in result.get('message', '').lower():
            print("    ✅ Валидация формата файла работает корректно")
            return True
        else:
            print(f"    ❌ Неожиданное сообщение об ошибке: {result.get('message')}")
            return False
    else:
        print(f"    ❌ Ожидалась ошибка 400, получен код: {response.status_code}")
        return False

def test_image_optimization(image_id):
    """Тест оптимизации изображений"""
    print("  ✓ Тест оптимизации изображений")
    
    base_url = "http://localhost:8000"
    
    # Получаем информацию об изображении
    response = requests.get(f"{base_url}/cms/api/images")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            images = result['images']
            test_image = next((img for img in images if img['id'] == image_id), None)
            
            if test_image:
                # Проверяем, что оптимизированное изображение существует
                optimized_path = test_image['path']
                if os.path.exists(optimized_path):
                    # Проверяем, что это WebP файл
                    if optimized_path.endswith('.webp'):
                        print("    ✅ Изображение оптимизировано в WebP формат")
                        
                        # Проверяем размеры оптимизированного изображения
                        with Image.open(optimized_path) as img:
                            width, height = img.size
                            if width <= 1920:  # Максимальная ширина
                                print(f"    ✅ Размеры оптимизированы: {width}x{height}")
                                return True
                            else:
                                print(f"    ❌ Ширина превышает лимит: {width}")
                                return False
                    else:
                        print(f"    ❌ Файл не в WebP формате: {optimized_path}")
                        return False
                else:
                    print(f"    ❌ Оптимизированный файл не найден: {optimized_path}")
                    return False
            else:
                print("    ❌ Тестовое изображение не найдено")
                return False
        else:
            print(f"    ❌ Ошибка получения списка изображений: {result.get('message')}")
            return False
    else:
        print(f"    ❌ HTTP ошибка при получении списка: {response.status_code}")
        return False

def test_image_management():
    """Тест управления изображениями"""
    print("  ✓ Тест управления изображениями")
    
    base_url = "http://localhost:8000"
    
    # Получаем список изображений
    response = requests.get(f"{base_url}/cms/api/images")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            images = result['images']
            print(f"    ✅ Получено {len(images)} изображений")
            
            # Проверяем структуру данных
            if images:
                image = images[0]
                required_fields = ['id', 'name', 'path', 'original_path', 'type', 'order']
                missing_fields = [field for field in required_fields if field not in image]
                
                if not missing_fields:
                    print("    ✅ Структура данных изображения корректна")
                    return images[0]['id']
                else:
                    print(f"    ❌ Отсутствуют поля: {missing_fields}")
                    return None
            else:
                print("    ⚠️ Нет изображений для тестирования")
                return None
        else:
            print(f"    ❌ Ошибка получения списка: {result.get('message')}")
            return None
    else:
        print(f"    ❌ HTTP ошибка: {response.status_code}")
        return None

def test_image_deletion(image_id):
    """Тест удаления изображения"""
    print("  ✓ Тест удаления изображения")
    
    base_url = "http://localhost:8000"
    
    # Удаляем изображение
    response = requests.delete(f"{base_url}/cms/api/images/{image_id}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("    ✅ Изображение удалено успешно")
            
            # Проверяем, что изображение действительно удалено
            response = requests.get(f"{base_url}/cms/api/images")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    images = result['images']
                    remaining_image = next((img for img in images if img['id'] == image_id), None)
                    if not remaining_image:
                        print("    ✅ Изображение полностью удалено из системы")
                        return True
                    else:
                        print("    ❌ Изображение все еще присутствует в списке")
                        return False
                else:
                    print(f"    ❌ Ошибка проверки удаления: {result.get('message')}")
                    return False
            else:
                print(f"    ❌ HTTP ошибка при проверке: {response.status_code}")
                return False
        else:
            print(f"    ❌ Ошибка удаления: {result.get('message')}")
            return False
    else:
        print(f"    ❌ HTTP ошибка при удалении: {response.status_code}")
        return False

def test_image_order_management():
    """Тест управления порядком изображений"""
    print("  ✓ Тест управления порядком изображений")
    
    base_url = "http://localhost:8000"
    
    # Загружаем несколько изображений для слайдера
    test_images = []
    for i in range(3):
        test_image = create_test_image(width=400 + i*100, height=300 + i*50)
        files = {'file': (f'slider_{i}.jpg', test_image, 'image/jpeg')}
        data = {'image_type': 'slider'}
        
        response = requests.post(f"{base_url}/cms/api/images/upload", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                test_images.append(result['image'])
    
    if len(test_images) >= 2:
        print(f"    ✅ Загружено {len(test_images)} изображений для тестирования порядка")
        
        # Тестируем изменение порядка
        first_image = test_images[0]
        new_order = 999
        
        form_data = {'new_order': str(new_order)}
        response = requests.put(f"{base_url}/cms/api/images/{first_image['id']}/order", data=form_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("    ✅ Порядок изображения обновлен")
                
                # Проверяем, что порядок действительно изменился
                response = requests.get(f"{base_url}/cms/api/images/by-type/slider")
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        images = result['images']
                        updated_image = next((img for img in images if img['id'] == first_image['id']), None)
                        if updated_image and updated_image['order'] == new_order:
                            print("    ✅ Порядок изображения корректно обновлен в БД")
                            
                            # Очищаем тестовые изображения
                            for img in test_images:
                                requests.delete(f"{base_url}/cms/api/images/{img['id']}")
                            
                            return True
                        else:
                            print("    ❌ Порядок изображения не обновился в БД")
                            return False
                    else:
                        print(f"    ❌ Ошибка получения изображений по типу: {result.get('message')}")
                        return False
                else:
                    print(f"    ❌ HTTP ошибка при получении изображений: {response.status_code}")
                    return False
            else:
                print(f"    ❌ Ошибка обновления порядка: {result.get('message')}")
                return False
        else:
            print(f"    ❌ HTTP ошибка при обновлении порядка: {response.status_code}")
            return False
    else:
        print("    ❌ Не удалось загрузить достаточно изображений для тестирования")
        return False

def test_cache_invalidation():
    """Тест инвалидации кэша"""
    print("  ✓ Тест инвалидации кэша изображений")
    
    base_url = "http://localhost:8000"
    
    # Загружаем изображение
    test_image = create_test_image()
    files = {'file': ('cache_test.jpg', test_image, 'image/jpeg')}
    data = {'image_type': 'logo'}
    
    response = requests.post(f"{base_url}/cms/api/images/upload", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            image_id = result['image']['id']
            print("    ✅ Изображение загружено для тестирования кэша")
            
            # Удаляем изображение (это должно инвалидировать кэш)
            response = requests.delete(f"{base_url}/cms/api/images/{image_id}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("    ✅ Изображение удалено, кэш должен быть инвалидирован")
                    
                    # Проверяем, что изображение больше не доступно
                    response = requests.get(f"{base_url}/cms/api/images")
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            images = result['images']
                            deleted_image = next((img for img in images if img['id'] == image_id), None)
                            if not deleted_image:
                                print("    ✅ Кэш корректно инвалидирован, изображение недоступно")
                                return True
                            else:
                                print("    ❌ Изображение все еще доступно после удаления")
                                return False
                        else:
                            print(f"    ❌ Ошибка проверки кэша: {result.get('message')}")
                            return False
                    else:
                        print(f"    ❌ HTTP ошибка при проверке кэша: {response.status_code}")
                        return False
                else:
                    print(f"    ❌ Ошибка удаления для теста кэша: {result.get('message')}")
                    return False
            else:
                print(f"    ❌ HTTP ошибка при удалении для теста кэша: {response.status_code}")
                return False
        else:
            print(f"    ❌ Ошибка загрузки для теста кэша: {result.get('message')}")
            return False
    else:
        print(f"    ❌ HTTP ошибка при загрузке для теста кэша: {response.status_code}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск автотеста управления изображениями")
    print("=" * 60)
    
    # Проверяем, что сервер запущен
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер не отвечает на /health")
            return False
    except requests.exceptions.RequestException:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен на localhost:8000")
        return False
    
    print("✅ Сервер доступен, начинаем тестирование")
    print()
    
    # Список тестов
    tests = [
        ("Валидация размера файла", test_image_size_validation),
        ("Валидация формата файла", test_image_format_validation),
        ("Загрузка корректного изображения", test_image_upload_validation),
        ("Управление изображениями", test_image_management),
        ("Оптимизация изображений", lambda: test_image_optimization(test_image_upload_validation())),
        ("Управление порядком", test_image_order_management),
        ("Инвалидация кэша", test_cache_invalidation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"  ✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"  ❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"  ❌ {test_name} - ОШИБКА: {e}")
        print()
    
    # Результаты
    print("=" * 60)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print(f"⚠️ {total - passed} тестов провалено")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
