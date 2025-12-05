import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def fake_gemini_key():
    """
    Para que los unit tests no fallen por falta del API key,
    simplemente colocamos un valor dummy.
    """
    os.environ["GEMINI_API_KEY"] = "dummy"
