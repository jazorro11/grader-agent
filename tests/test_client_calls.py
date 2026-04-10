from unittest.mock import MagicMock, patch

import pytest

from grader_agent.llm import client_calls


@patch.object(client_calls, "with_openai_rate_limit_retry")
def test_chat_completion_json_content_raises_on_empty_message(mock_retry):
    mock_client = MagicMock()
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content="   "))]
    mock_retry.return_value = resp
    with pytest.raises(ValueError, match="empty message"):
        client_calls.chat_completion_json_content(
            mock_client,
            system="s",
            user="u",
            temperature=0,
            kind="escala",
        )


@patch.object(client_calls, "with_openai_rate_limit_retry")
def test_chat_completion_json_content_raises_on_no_choices(mock_retry):
    mock_client = MagicMock()
    resp = MagicMock()
    resp.choices = []
    mock_retry.return_value = resp
    with pytest.raises(ValueError, match="no choices"):
        client_calls.chat_completion_json_content(
            mock_client,
            system="s",
            user="u",
            temperature=0,
            kind="puntaje",
        )
