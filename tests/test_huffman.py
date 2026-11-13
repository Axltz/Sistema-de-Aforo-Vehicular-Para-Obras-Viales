import json

from src.analytics.huffman import compress_text_huffman, decompress_huffman


def test_compress_empty_text_returns_empty():
    compressed, codes = compress_text_huffman("")
    assert compressed == ""
    assert codes == {}


def test_huffman_roundtrip(tmp_path):
    payload = {"report_generated": "2026-01-01 12:00:00", "total_count": 42}
    original = json.dumps(payload, ensure_ascii=False)

    binary_text, code_table = compress_text_huffman(original)
    assert binary_text
    assert code_table

    # Repack the bit string into bytes exactly like the exporter does.
    data = bytearray()
    for i in range(0, len(binary_text), 8):
        chunk = binary_text[i:i + 8].ljust(8, "0")
        data.append(int(chunk, 2))

    bin_path = tmp_path / "report.bin"
    dict_path = tmp_path / "report_dict.json"
    bin_path.write_bytes(bytes(data))
    dict_path.write_text(json.dumps(code_table), encoding="utf-8")

    recovered = decompress_huffman(bin_path, dict_path)
    assert recovered == payload
