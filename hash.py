from werkzeug.security import generate_password_hash

print(generate_password_hash("rianapass", method="pbkdf2:sha256"))