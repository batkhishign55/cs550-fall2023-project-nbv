import struct
import hashlib

class Transaction:
    def __init__(self, sender_address, recipient_address, value, timestamp, transaction_id, signature):
        self.sender_address = sender_address
        self.recipient_address = recipient_address
        self.value = value
        self.timestamp = timestamp
        self.transaction_id = transaction_id
        self.signature = signature

    def pack(self):
        return struct.pack("<32s32sdq16s32s", 
                           self.sender_address.encode('utf-8'), 
                           self.recipient_address.encode('utf-8'), 
                           self.value, 
                           self.timestamp, 
                           self.transaction_id.encode('utf-8'), 
                           self.signature.encode('utf-8'))

    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack("<32s32sdq16s32s", data)
        return cls(unpacked_data[0].decode('utf-8').rstrip('\x00'), 
                   unpacked_data[1].decode('utf-8').rstrip('\x00'), 
                   unpacked_data[2], 
                   unpacked_data[3], 
                   unpacked_data[4].decode('utf-8'), 
                   unpacked_data[5].decode('utf-8'))

class Block:
    def __init__(self, version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, transactions):
        self.version = version
        self.prev_block_hash = prev_block_hash
        self.block_id = block_id
        self.timestamp = timestamp
        self.difficulty_target = difficulty_target
        self.nonce = nonce
        self.transactions = transactions

    def pack_header(self):
        return struct.pack("<H32sIqHqI", 
                           self.version, 
                           self.prev_block_hash.encode('utf-8'), 
                           self.block_id, 
                           self.timestamp, 
                           self.difficulty_target, 
                           self.nonce, 
                           len(self.transactions))

    def calculate_hash(self):
        header = self.pack_header()
        return hashlib.sha256(header).hexdigest()

    def mine_block(self):
        while int(self.calculate_hash(), 16) > 2 ** (256 - self.difficulty_target):
            self.nonce += 1

    def pack(self):
        header = self.pack_header()
        transactions_data = b"".join(transaction.pack() for transaction in self.transactions)
        return struct.pack(f"<{len(header)}s64s{len(transactions_data)}s", header, b"", transactions_data)

    @classmethod
    def unpack(cls, data):
        header_size = struct.calcsize("<H32sIqHqI")
        header, _, transactions_data = struct.unpack(f"<{header_size}s64s{len(data)-header_size-64}s", data)
        header_data = struct.unpack("<H32sIqHqI", header)
        transactions = [Transaction.unpack(transactions_data[i:i+128]) for i in range(0, len(transactions_data), 128)]
        return cls(header_data[0], 
                   header_data[1].decode('utf-8'), 
                   header_data[2], 
                   header_data[3], 
                   header_data[4], 
                   header_data[5], 
                   transactions)


# Example Usage:

# Create Transactions
# transaction1 = Transaction("Sender1", "Recipient1", 10.5, 1637997900, "ID1", "Signature1")
# transaction2 = Transaction("Sender2", "Recipient2", 5.0, 1637998000, "ID2", "Signature2")

# # Create Block with Transactions
# block = Block(1, "159f4ef0bcc5fa42fc90bdf7acfd7308bf9b3dacd501d23f3cff799d3f6b3234", 123, 1637998100, 3, 123456, [transaction1, transaction2])

# # Mine the Block
# # block.mine_block()

# # Serialize and Deserialize Block
# serialized_block = block.pack()
# deserialized_block = Block.unpack(serialized_block)

# # Print Results
# print("Original Block:")
# print(block.__dict__)

# print("\nCalculated Hash:")
# print(block.calculate_hash())

# print("\nSerialized Block:")
# print(serialized_block)

# print("\nDeserialized Block:")
# print(deserialized_block.__dict__)

# transactions = deserialized_block.transactions

# # Print the details of each transaction
# # for transaction in transactions:
# for transaction in transactions:
#     print(f"  Sender Address: {transaction.sender_address}")
#     print(f"  Recipient Address: {transaction.recipient_address}")
#     print(f"  Value: {transaction.value}")
#     print(f"  Timestamp: {transaction.timestamp}")
#     print(f"  Transaction ID: {transaction.transaction_id}")
#     print(f"  Signature: {transaction.signature}")