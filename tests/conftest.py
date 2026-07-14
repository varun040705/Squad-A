import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_anthropic_client(monkeypatch):
    """
    Automatically mocks the Anthropic API client globally for all tests.
    This prevents live API requests and saves credits during test runs.
    """
    mock_client = MagicMock()

    # Simulate Claude's JSON response structure
    mock_message = MagicMock()
    mock_message.content = [
        MagicMock(text='{"primary_defect": "structural_crack", "confidence": "high", "roles_agreed": 3, "flag_score": 85, "recommended_action": "escalate"}')
    ]

    # Configure the mock to return this message when client.messages.create() is called
    mock_client.messages.create.return_value = mock_message

    # Force the patched 'anthropic.Anthropic' class to return our mock client
    monkeypatch.setattr("anthropic.Anthropic", lambda *args, **kwargs: mock_client)

    return mock_client
