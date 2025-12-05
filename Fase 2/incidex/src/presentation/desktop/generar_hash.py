import bcrypt

def generar_hash(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

if __name__ == "__main__":
    password = input("Contraseña en texto plano: ")
    print("\nHash generado:")
    print(generar_hash(password))
