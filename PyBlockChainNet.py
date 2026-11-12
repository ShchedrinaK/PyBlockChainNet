import hashlib
import time
import threading


# ==========================================
# Шаг 1 и 2: Модификация класса Block
# ==========================================
class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()


# ==========================================
# Шаг 3: Обновление класса Blockchain
# ==========================================
class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = [self.create_genesis_block()]
        self.difficulty = difficulty

    def create_genesis_block(self):
        return Block(0, 0, "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        latest_block = self.get_latest_block()
        new_block = Block(latest_block.index + 1, time.time(), data, latest_block.hash)
        print(f"Начат майнинг блока {new_block.index}...")

        start = time.time()
        new_block.mine_block(self.difficulty)
        elapsed = time.time() - start

        # УЛУЧШЕНИЕ: Добавлен лог успеха с nonce, хешем и временем
        print(
            f"Блок {new_block.index} успешно намайнен. Nonce: {new_block.nonce}, Hash: {new_block.hash[:10]}..., время: {elapsed:.2f} сек.")
        self.chain.append(new_block)

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                print(f"Ошибка: Хеш блока {i} не соответствует данным.")
                return False
            if current_block.previous_hash != previous_block.hash:
                print(f"Ошибка: Блок {i} не связан с блоком {i - 1}.")
                return False
            if not current_block.hash.startswith('0' * self.difficulty):
                print(f"Ошибка: Блок {i} не удовлетворяет сложности PoW.")
                return False
        return True


# ==========================================
# Шаг 4: Модификация класса Node
# ==========================================
class Node:
    def __init__(self, node_id, blockchain):
        self.node_id = node_id
        self.blockchain = blockchain
        self.peers = []

    def connect(self, peer_node):
        self.peers.append(peer_node)

    def create_and_broadcast_block(self, data):
        latest = self.blockchain.get_latest_block()
        new_block = Block(latest.index + 1, time.time(), data, latest.hash)

        print(f"[Узел {self.node_id}] Начинает майнинг блока {new_block.index}...")
        new_block.mine_block(self.blockchain.difficulty)
        print(f"[Узел {self.node_id}] УСПЕШНО намайнил блок {new_block.index}! Nonce: {new_block.nonce}")

        if self.blockchain.get_latest_block().hash == new_block.previous_hash:
            self.blockchain.chain.append(new_block)
            print(f"[Узел {self.node_id}] Добавил блок в свою цепочку. Распространяет...")
            for peer in self.peers:
                peer.receive_block(new_block)
        else:
            print(f"[Узел {self.node_id}] ОТКЛОНЯЕТ свой блок: пока майнили, сеть ушла вперед (race condition).")

    def receive_block(self, block):
        latest = self.blockchain.get_latest_block()
        if block.previous_hash == latest.hash:
            if block.hash.startswith('0' * self.blockchain.difficulty) and block.hash == block.calculate_hash():
                self.blockchain.chain.append(block)
                print(f"[Узел {self.node_id}] ПРИНЯЛ блок {block.index} от сети.")
            else:
                print(f"[Узел {self.node_id}] Отклонил блок: неверный PoW или хеш.")
        elif block.index <= latest.index:
            pass
        else:
            print(f"[Узел {self.node_id}] Отклонил блок: цепочка уже продвинулась (race condition).")


# ==========================================
# Шаги 5 и 6: Симуляция и тестирование
# ==========================================
if __name__ == "__main__":
    print("=== Шаг 5: Симуляция одновременного майнинга ===")
    difficulty = 4

    node1 = Node("A", Blockchain(difficulty))
    node2 = Node("B", Blockchain(difficulty))
    node3 = Node("C", Blockchain(difficulty))

    node1.connect(node2);
    node1.connect(node3)
    node2.connect(node1);
    node2.connect(node3)
    node3.connect(node1);
    node3.connect(node2)

    print(f"Узлы A, B и C одновременно пытаются намайнить блок с index=1 (сложность {difficulty})...\n")

    thread1 = threading.Thread(target=node1.create_and_broadcast_block, args=("Транзакция A",))
    thread2 = threading.Thread(target=node2.create_and_broadcast_block, args=("Транзакция B",))
    thread3 = threading.Thread(target=node3.create_and_broadcast_block, args=("Транзакция C",))

    thread1.start()
    thread2.start()
    thread3.start()
    thread1.join()
    thread2.join()
    thread3.join()

    print(f"\nИтоговая длина цепочки у Узла A: {len(node1.blockchain.chain)}")
    print(f"Валидность цепочки A: {node1.blockchain.is_valid()}")

    print("\n=== Шаг 6: Проверка защиты от подделки ===")
    print("Добавляем блоки 2 и 3 в цепочку для теста...")
    node1.blockchain.add_block("Транзакция 2")
    node1.blockchain.add_block("Транзакция 3")

    print("\n[Взлом] Изменяем данные в блоке 1...")
    node1.blockchain.chain[1].data = "Взломанные данные"

    is_valid = node1.blockchain.is_valid()
    print(f"Валидность цепочки после подделки (без перемайнинга): {is_valid}")

    print("\n[Атака] Начинаем перемайнинг скомпрометированного блока и всех последующих...")
    attack_start_time = time.time()

    for i in range(1, len(node1.blockchain.chain)):
        print(f"\n[Узел A] Перемайнинг блока {i}...")
        # Сбрасываем nonce и пересчитываем хеш (имитация того, что злоумышленник
        # не может оставить старый nonce, так как данные изменились)
        node1.blockchain.chain[i].nonce = 0
        node1.blockchain.chain[i].hash = node1.blockchain.chain[i].calculate_hash()

        # Замеряем время майнинга каждого блока отдельно
        block_start = time.time()
        node1.blockchain.chain[i].mine_block(difficulty)
        block_elapsed = time.time() - block_start

        # Лог успешного перемайнинга с nonce, хешем и временем
        print(f"[Узел A] Блок {i} перемайнен. Новый nonce: {node1.blockchain.chain[i].nonce}, "
              f"Hash: {node1.blockchain.chain[i].hash[:10]}..., время: {block_elapsed:.2f} сек.")

        # Обновляем previous_hash у следующего блока, так как хеш текущего изменился
        if i + 1 < len(node1.blockchain.chain):
            node1.blockchain.chain[i + 1].previous_hash = node1.blockchain.chain[i].hash
            print(f"[Узел A] Обновлен previous_hash для блока {i + 1}.")

    total_time = time.time() - attack_start_time
    print(f"\nОбщее время перемайнинга {len(node1.blockchain.chain) - 1} блоков: {total_time:.2f} сек.")
    print("В реальной сети это заняло бы колоссальное время и энергию.")
    print(f"Валидность цепочки после перемайнинга: {node1.blockchain.is_valid()}")