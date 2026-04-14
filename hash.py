from werkzeug.security import generate_password_hash

# Example usage
print(generate_password_hash("rianapass", method="pbkdf2:sha256"))
print(generate_password_hash("zyklonz", method="pbkdf2:sha256"))