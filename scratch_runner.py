import pytest
import sys

if __name__ == "__main__":
    print("Running Phase 6 Test Suite...")
    ret = pytest.main(["-v", "backend/tests/test_phase6_rag_memory_tools.py"])
    sys.exit(ret)
