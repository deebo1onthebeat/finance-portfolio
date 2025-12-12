import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from jose import JWTError, jwt

# --- BCRYPT PASSWORD HASHING ---

def get_password_hash(password: str) -> str:
    """Хеширует пароль с использованием bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли пароль с хешем."""
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

# --- JWT TOKEN HANDLING ---

# Секретный ключ. В реальном проекте его нужно брать из .env!
SECRET_KEY = "my_super_secret_key_that_should_be_in_env_file"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Время жизни токена (30 минут)

def create_access_token(data: dict):
    """Создает новый JWT токен."""
    to_encode = data.copy()
    # Устанавливаем время жизни токена
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Кодируем токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Проверяет токен и возвращает email, если токен валиден."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Достаем email из "полезной нагрузки" токена
        email: str = payload.get("sub")
        if email is None:
            # Если email нет - это ошибка
            raise credentials_exception
        return email
    except JWTError:
        # Если токен просрочен или невалиден
        raise credentials_exception