import heapq
import json
from collections import Counter


class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(text):
    frequencies = Counter(text)
    heap = [HuffmanNode(char, freq) for char, freq in frequencies.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left_node = heapq.heappop(heap)
        right_node = heapq.heappop(heap)
        parent_node = HuffmanNode(None, left_node.freq + right_node.freq)
        parent_node.left = left_node
        parent_node.right = right_node
        heapq.heappush(heap, parent_node)

    return heap[0] if heap else None


def generate_codes(node, current_code="", codes=None):
    if codes is None:
        codes = {}
    if node is not None:
        if node.char is not None:
            codes[node.char] = current_code
        generate_codes(node.left, current_code + "0", codes)
        generate_codes(node.right, current_code + "1", codes)
    return codes


def compress_text_huffman(text):
    if not text:
        return "", {}
    root = build_huffman_tree(text)
    code_table = generate_codes(root)
    compressed_text = "".join([code_table[char] for char in text])
    return compressed_text, code_table


def decompress_huffman(bin_path, dict_path):
    with open(dict_path, "r", encoding="utf-8") as f:
        codes = json.load(f)
    reversed_codes = {v: k for k, v in codes.items()}

    with open(bin_path, "rb") as f:
        byte_content = f.read()

    bit_string = "".join([f"{byte:08b}" for byte in byte_content])

    decoded_text = ""
    current_code = ""
    for bit in bit_string:
        current_code += bit
        if current_code in reversed_codes:
            decoded_text += reversed_codes[current_code]
            current_code = ""

    # Find the last closing '}' of the real JSON to trim the extra characters
    # produced by the padding bits.
    json_end = decoded_text.rfind('}') + 1
    clean_text = decoded_text[:json_end]

    return json.loads(clean_text)
