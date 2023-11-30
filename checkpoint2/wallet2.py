from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
import base58
import yaml

def generate_key_pair():
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()
    return private_key, public_key

def save_keys_to_yaml(private_key, public_key, filename):
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    keys_data = {
        'private_key': base58.b58encode(private_key_bytes).decode('utf-8'),
        'public_key': base58.b58encode(public_key_bytes).decode('utf-8')
    }

    with open(filename, 'w') as file:
        yaml.dump(keys_data, file)

def load_keys_from_yaml(filename):
    with open(filename, 'r') as file:
        keys_data = yaml.safe_load(file)

    private_key_bytes = base58.b58decode(keys_data['private_key'])
    public_key_bytes = base58.b58decode(keys_data['public_key'])

    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
        backend=default_backend()
    )

    public_key = serialization.load_pem_public_key(
        public_key_bytes,
        backend=default_backend()
    )

    return private_key, public_key

def sign_message(private_key, message):
    signature = private_key.sign(
        message.encode('utf-8'),
        ec.ECDSA(hashes.SHA256())
    )
    return base58.b58encode(signature).decode('utf-8')

def verify_signature(public_key, message, signature):
    try:
        signature_bytes = base58.b58decode(signature)
        public_key.verify(
            signature_bytes,
            message.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except Exception:
        return False

# Example usage:
private_key, public_key = generate_key_pair()
save_keys_to_yaml(private_key, public_key, 'dsc-key.yaml')

loaded_private_key, loaded_public_key = load_keys_from_yaml('dsc-key.yaml')

message_to_sign = "Hello, World!"
signature = sign_message(private_key, message_to_sign)

verification_result = verify_signature(loaded_public_key, message_to_sign, signature)
print(f"Verification Result: {verification_result}")
