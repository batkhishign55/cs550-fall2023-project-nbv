import struct
import time

class BlockHeader:
    def __init__(self, version, prev_block_hash, block_id, timestamp, difficulty_target, nonce):
        self.version = version
        self.prev_block_hash = prev_block_hash
        self.block_id = block_id
        self.timestamp = timestamp
        self.difficulty_target = difficulty_target
        self.nonce = nonce

    def pack(self):
        # Pack the block header data into bytes
        packed_header = struct.pack(
            'H32sIQHQ',
            self.version,
            self.prev_block_hash.encode('utf-8'),
            self.block_id,
            self.timestamp,
            self.difficulty_target,
            self.nonce
        )
        return packed_header

    @classmethod
    def unpack(cls, packed_header):
        # Unpack the bytes into a block header object
        unpacked_data = struct.unpack('H32sIQHQ', packed_header)
        return cls(
            version=unpacked_data[0],
            prev_block_hash=unpacked_data[1].decode('utf-8').rstrip('\x00'),
            block_id=unpacked_data[2],
            timestamp=unpacked_data[3],
            difficulty_target=unpacked_data[4],
            nonce=unpacked_data[5]
        )

class Block:
    def __init__(self, version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, transactions):
        self.version = version
        self.prev_block_hash = prev_block_hash
        self.block_id = block_id
        self.timestamp = timestamp
        self.difficulty_target = difficulty_target
        self.nonce = nonce
        self.transactions = transactions

    def pack(self):
        # Pack the block data into bytes
        header = BlockHeader(
            version=self.version,
            prev_block_hash=self.prev_block_hash,
            block_id=self.block_id,
            timestamp=self.timestamp,
            difficulty_target=self.difficulty_target,
            nonce=self.nonce
        )
        packed_header = header.pack()

        # Pack the block size, transaction counter, reserved, and transactions
        packed_block = struct.pack(
            'I56sI64s',
            len(packed_header) + 4 + 4 + len(self.transactions) * 128,
            packed_header,
            len(self.transactions),
            b''  # Placeholder for reserved data
        )

        # Append each transaction to the block
        for transaction in self.transactions:
            packed_block += transaction.pack()

        return packed_block

    @classmethod
    def unpack(cls, packed_block):
        # Unpack the bytes into a block object
        unpacked_header = struct.unpack('I56sI64s', packed_block[:124])
        header = BlockHeader.unpack(unpacked_header[1])

        # Extract the transactions
        transactions = []
        for i in range(unpacked_header[2]):
            start_index = 128 + i * 128
            end_index = start_index + 128
            transactions.append(Transaction.unpack(packed_block[start_index:end_index]))

        return cls(
            version=header.version,
            prev_block_hash=header.prev_block_hash,
            block_id=header.block_id,
            timestamp=header.timestamp,
            difficulty_target=header.difficulty_target,
            nonce=header.nonce,
            transactions=transactions
        )
