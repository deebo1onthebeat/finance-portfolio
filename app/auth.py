import bcrypt

def get_password_hash(password: str) -> str:
    """Хеширует пароль с использованием bcrypt."""
    # 1. Превращаем пароль в байты
    password_bytes = password.encode('utf-8')
    # 2. Генерируем "соль" (случайная строка для безопасности)
    salt = bcrypt.gensalt()
    # 3. Хешируем и превращаем обратно в строку для записи в БД
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли пароль с хешем."""
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)