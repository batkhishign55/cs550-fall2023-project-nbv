import struct

class Transaction:
    def __init__(self, sender_address, recipient_address, value, nonce, reserved, signature):
        self.sender_address = sender_address
        self.recipient_address = recipient_address
        self.value = value
        self.nonce = nonce
        self.reserved = reserved
        self.signature = signature

    def pack(self):
        # Pack the transaction data into bytes
        packed_transaction = struct.pack(
            '32s32sdd16s32s',
            self.sender_address.encode('utf-8'),
            self.recipient_address.encode('utf-8'),
            self.value,
            self.nonce,
            self.reserved.encode('utf-8'),
            self.signature.encode('utf-8')
        )
        return packed_transaction

    @classmethod
    def unpack(cls, packed_transaction):
        # Unpack the bytes into a transaction object
        unpacked_data = struct.unpack('32s32sdd16s32s', packed_transaction)
        return cls(
            sender_address=unpacked_data[0].decode('utf-8').rstrip('\x00'),
            recipient_address=unpacked_data[1].decode('utf-8').rstrip('\x00'),
            value=unpacked_data[2],
            nonce=unpacked_data[3],
            reserved=unpacked_data[4].decode('utf-8').rstrip('\x00'),
            signature=unpacked_data[5].decode('utf-8').rstrip('\x00')
        )

