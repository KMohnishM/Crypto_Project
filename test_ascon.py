#!/usr/bin/env python3
import ascon
import json

# Test ascon library
key = bytes.fromhex('0ba058466e8f56e85f6ba525bb1722e1')
nonce = b'1234567890123456'
plain = json.dumps({'test': 'data'}).encode()

print("Key:", key.hex())
print("Nonce:", nonce.hex())
print("Plaintext:", plain)

ct = ascon.encrypt(key, nonce, b'', plain)
print("Ciphertext length:", len(ct))
print("Ciphertext first 20 bytes:", ct[:20].hex())

pt = ascon.decrypt(key, nonce, b'', ct)
print("Decrypted:", pt)
print("Success!", pt == plain)
