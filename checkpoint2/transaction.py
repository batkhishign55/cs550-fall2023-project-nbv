import struct
import time
class Transaction:
    def __init__(self, transaction_id, sender_public_address, recipient_public_address, value, nonce, signature):
        self.transaction_id = transaction_id
        self.sender_public_address = sender_public_address
        self.recipient_public_address = recipient_public_address
        self.value = value
        self.nonce = nonce
        self.signature = signature

    def pack(self):
        # Pack the transaction data into bytes
        packed_transaction = struct.pack(
            '32s32s32sdQ32s',
            self.transaction_id.encode('utf-8'),
            self.sender_public_address.encode('utf-8'),
            self.recipient_public_address.encode('utf-8'),
            self.value,
            self.nonce,
            self.signature.encode('utf-8')
        )
        return packed_transaction

    @classmethod
    def unpack(cls, packed_transaction):
        # Unpack the bytes into a transaction object
        unpacked_data = struct.unpack('32s32s32sdQ32s', packed_transaction)
        return cls(
            transaction_id=unpacked_data[0].decode('utf-8').rstrip('\x00'),
            sender_public_address=unpacked_data[1].decode('utf-8').rstrip('\x00'),
            recipient_public_address=unpacked_data[2].decode('utf-8').rstrip('\x00'),
            value=unpacked_data[3],
            nonce=unpacked_data[4],
            signature=unpacked_data[5].decode('utf-8').rstrip('\x00')
        )
