import os, random, string
from datetime import datetime
from core.database import get_connection
import hashlib

class TxtUserManager:
    """
    Gestor de usuarios utilizando SQLite en lugar de txt plano.
    Mantenemos el nombre TxtUserManager por compatibilidad temporal,
    pero internamente usa la base de datos.
    """

    def __init__(self, filepath=None):
        pass
        
    def _hash_password(self, password):
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def authenticate(self, username, password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password, is_active, failed_attempts, locked_until FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
            
        stored_pw = row['password']
        is_active = row['is_active']
        failed_attempts = row['failed_attempts'] if 'failed_attempts' in row.keys() else 0
        locked_until = row['locked_until'] if 'locked_until' in row.keys() else None
        
        if is_active == 0:
            conn.close()
            return False
            
        # Verificar si está bloqueado temporalmente
        if locked_until:
            try:
                locked_time = datetime.strptime(locked_until, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < locked_time:
                    conn.close()
                    raise Exception("Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intente más tarde.")
                else:
                    # El bloqueo expiró
                    cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = ?", (username,))
                    conn.commit()
            except ValueError:
                pass
        
        # Soportar contraseñas antiguas
        is_valid = False
        import bcrypt
        if len(stored_pw) == 64 and "$" not in stored_pw: # SHA-256
            is_valid = (stored_pw == hashlib.sha256(password.encode()).hexdigest())
            if is_valid:
                # Upgrade hash a bcrypt
                new_hash = self._hash_password(password)
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hash, username))
                conn.commit()
        elif stored_pw.startswith("$2b$") or stored_pw.startswith("$2a$"):
            is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_pw.encode('utf-8'))
        else:
            is_valid = (stored_pw == password)
            if is_valid:
                # Upgrade hash a bcrypt
                new_hash = self._hash_password(password)
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hash, username))
                conn.commit()
            
        if is_valid:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute("UPDATE users SET last_login = ?, failed_attempts = 0, locked_until = NULL WHERE username = ?", (now, username))
            conn.commit()
            conn.close()
            return True
        else:
            # Incrementar intentos fallidos
            failed_attempts += 1
            if failed_attempts >= 3:
                # Bloquear por 5 minutos
                from datetime import timedelta
                lock_time = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE username = ?", (failed_attempts, lock_time, username))
                conn.commit()
                conn.close()
                raise Exception("Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intente en 5 minutos.")
            else:
                cursor.execute("UPDATE users SET failed_attempts = ? WHERE username = ?", (failed_attempts, username))
                conn.commit()
            
            conn.close()
            return False

    def exists(self, username):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def add_user_plain(self, username, password):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            role = 'admin' if username == 'Administrador' else 'usuario'
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute("INSERT INTO users (username, password, role, created_at, is_active) VALUES (?, ?, ?, ?, 1)", 
                          (username, self._hash_password(password), role, now))
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()

    def generate_and_save_secure_password(self, username):
        if self.exists(username):
            raise ValueError("El usuario ya tiene una contraseña.")
        chars = string.ascii_letters + string.digits
        password = "".join(random.choice(chars) for _ in range(8))
        self.add_user_plain(username, password)
        return password

    def get_password(self, username):
        # NOTE: With hashing, we can't return the plaintext password anymore!
        # In a real app this wouldn't be supported, but since the old app uses it 
        # to show the admin the PIN, we need to adapt it. 
        # For this refactor, we just inform the admin that they can only reset it.
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise ValueError("El usuario no existe.")
            
        # Para contraseñas nuevas, se devuelve un mensaje ya que no se pueden desencriptar
        pw = row['password']
        if len(pw) == 64: # SHA-256 length
            return "[Cifrada] - Use el botón de Resetear"
        return pw # Fallback for old plaintext ones

    def reset_password(self, username):
        if not self.exists(username):
            raise ValueError("El usuario no existe.")
            
        chars = string.ascii_letters + string.digits
        new_pin = "".join(random.choice(chars) for _ in range(8))
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", 
                      (self._hash_password(new_pin), username))
        conn.commit()
        conn.close()
        return new_pin

    def get_all_users(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, is_active, created_at, last_login FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def toggle_user_status(self, username):
        if username == 'Administrador':
            raise ValueError("No se puede desactivar al Administrador principal.")
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            new_status = 0 if row['is_active'] == 1 else 1
            cursor.execute("UPDATE users SET is_active = ? WHERE username = ?", (new_status, username))
            conn.commit()
        conn.close()