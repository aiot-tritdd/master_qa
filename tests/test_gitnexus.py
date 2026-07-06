from qa.gitnexus import symbol_hash

def test_symbol_hash_stable():
    assert symbol_hash(["a", "b"]) == symbol_hash(["a", "b"])

def test_symbol_hash_changes():
    assert symbol_hash(["a"]) != symbol_hash(["a", "b"])
