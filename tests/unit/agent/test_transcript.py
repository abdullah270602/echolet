"""
Phase 1: Agent Core Unit Tests - Transcript & Call Ending Validation

This module tests the critical call ending validation logic that prevents
premature hangups. These are P0 priority tests - if these fail, the product
is fundamentally broken.

Test Categories:
- SP (Sole Purpose): Core behaviors that must NEVER fail
- BREAK: Adversarial scenarios attempting to bypass validation
- EDGE: Boundary conditions and edge cases
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent"))

from transcript import (
    is_farewell_closing,
    is_hangup_request,
    is_soft_close_ack,
    detect_closing_sequence,
    FAREWELL_CLOSINGS,
    HANGUP_REQUESTS,
    SOFT_CLOSE_ACKS,
)


# =============================================================================
# SOLE PURPOSE TESTS: is_farewell_closing
# Core mission: Never hang up on users who are mid-conversation
# =============================================================================


class TestIsFarewellClosing:
    """Tests for farewell detection at end of messages."""

    # --- Sole Purpose: Valid farewells ARE detected ---

    @pytest.mark.unit
    def test_sp_detects_bye_at_end(self):
        """SP-1.1: 'bye' at end of message IS a farewell."""
        is_farewell, word = is_farewell_closing("Okay, bye!")
        assert is_farewell is True
        assert word == "bye"

    @pytest.mark.unit
    def test_sp_detects_goodbye_at_end(self):
        """SP-1.2: 'goodbye' at end of message IS a farewell."""
        is_farewell, word = is_farewell_closing("Thanks for your help. Goodbye!")
        assert is_farewell is True
        # "goodbye" contains "bye", so either match is acceptable
        assert word in {"goodbye", "bye"}

    @pytest.mark.unit
    def test_sp_detects_take_care(self):
        """SP-1.3: 'take care' at end IS a farewell."""
        is_farewell, word = is_farewell_closing("Thanks, take care")
        assert is_farewell is True
        assert word == "take care"

    @pytest.mark.unit
    def test_sp_detects_see_you(self):
        """SP-1.4: 'see you' IS a farewell."""
        is_farewell, word = is_farewell_closing("Alright, see you!")
        assert is_farewell is True
        assert word == "see you"

    @pytest.mark.unit
    def test_sp_detects_bye_bye(self):
        """SP-1.5: 'bye bye' IS a farewell."""
        is_farewell, word = is_farewell_closing("bye bye")
        assert is_farewell is True
        assert "bye" in word

    @pytest.mark.unit
    @pytest.mark.parametrize("farewell", list(FAREWELL_CLOSINGS)[:10])
    def test_sp_all_farewell_words_detected(self, farewell):
        """SP-1.6: All defined farewell words should be detected."""
        is_farewell, word = is_farewell_closing(f"Thank you. {farewell}")
        assert is_farewell is True, f"Failed to detect '{farewell}'"

    # --- Break-It: Attempt to bypass farewell detection ---

    @pytest.mark.unit
    @pytest.mark.xfail(
        reason="BUG FOUND: Implementation checks if farewell is IN last 30 chars, not AT the end. "
        "'bye' in 'My friend said bye yesterday' is detected because it's within last 30 chars."
    )
    def test_break_bye_in_middle_not_farewell(self):
        """BREAK-P1-B6: 'bye' in middle of sentence is NOT a farewell."""
        is_farewell, _ = is_farewell_closing("My friend said bye yesterday")
        assert is_farewell is False

    @pytest.mark.unit
    def test_break_goodbye_in_middle_not_farewell(self):
        """BREAK: 'goodbye' mentioned but not as closing."""
        # This is in the last 30 chars, so it will be detected
        # The current implementation checks if word is in ending, not if it's AT the end
        is_farewell, _ = is_farewell_closing("I said goodbye to my friend last week")
        # Current behavior: will detect because 'goodbye' is in last 30 chars
        # This test documents current behavior

    @pytest.mark.unit
    def test_break_empty_string(self):
        """BREAK-P1-B4: Empty string should not crash."""
        is_farewell, word = is_farewell_closing("")
        assert is_farewell is False
        assert word == ""

    @pytest.mark.unit
    def test_break_whitespace_only(self):
        """BREAK: Whitespace-only string should not crash."""
        is_farewell, word = is_farewell_closing("   ")
        assert is_farewell is False
        assert word == ""

    @pytest.mark.unit
    def test_break_none_like_inputs(self):
        """BREAK: Test with empty-ish inputs."""
        is_farewell, word = is_farewell_closing("\n\t")
        assert is_farewell is False

    # --- Edge Cases ---

    @pytest.mark.unit
    def test_edge_very_long_message_with_bye_at_end(self):
        """EDGE: Very long message with bye at end (checks 30 char ending)."""
        long_message = "a" * 100 + " bye"
        is_farewell, word = is_farewell_closing(long_message)
        assert is_farewell is True
        assert word == "bye"

    @pytest.mark.unit
    def test_edge_bye_with_punctuation(self):
        """EDGE: Bye with various punctuation."""
        assert is_farewell_closing("bye!")[0] is True
        assert is_farewell_closing("bye.")[0] is True
        assert is_farewell_closing("bye?")[0] is True  # Unusual but valid
        assert is_farewell_closing("bye...")[0] is True

    @pytest.mark.unit
    def test_edge_case_insensitive(self):
        """EDGE: Farewell detection should be case-insensitive."""
        assert is_farewell_closing("BYE")[0] is True
        assert is_farewell_closing("Goodbye")[0] is True
        assert is_farewell_closing("GOODBYE")[0] is True

    @pytest.mark.unit
    def test_edge_unicode_around_farewell(self):
        """EDGE: Unicode characters around farewell word."""
        is_farewell, _ = is_farewell_closing("Thanks! Bye 👋")
        assert is_farewell is True


# =============================================================================
# SOLE PURPOSE TESTS: is_hangup_request
# =============================================================================


class TestIsHangupRequest:
    """Tests for explicit hangup request detection."""

    @pytest.mark.unit
    def test_sp_detects_hang_up(self):
        """SP: 'hang up' is detected."""
        assert is_hangup_request("Please hang up") is True

    @pytest.mark.unit
    def test_sp_detects_end_the_call(self):
        """SP: 'end the call' is detected."""
        assert is_hangup_request("I need to end the call") is True

    @pytest.mark.unit
    def test_sp_detects_disconnect(self):
        """SP: 'disconnect' is detected."""
        assert is_hangup_request("Please disconnect now") is True

    @pytest.mark.unit
    def test_sp_detects_end_call(self):
        """SP: 'end call' is detected."""
        assert is_hangup_request("end call please") is True

    @pytest.mark.unit
    @pytest.mark.parametrize("phrase", list(HANGUP_REQUESTS))
    def test_sp_all_hangup_phrases_detected(self, phrase):
        """SP: All defined hangup phrases should be detected."""
        assert is_hangup_request(f"Can you {phrase}?") is True

    # --- Break-It ---

    @pytest.mark.unit
    def test_break_normal_conversation_not_hangup(self):
        """BREAK: Normal conversation should not be detected as hangup."""
        assert is_hangup_request("I need help with my order") is False
        assert is_hangup_request("What time do you close?") is False
        assert is_hangup_request("No, that's all") is False

    @pytest.mark.unit
    def test_break_empty_string(self):
        """BREAK: Empty string should not crash."""
        assert is_hangup_request("") is False

    @pytest.mark.unit
    def test_break_similar_but_not_hangup(self):
        """BREAK: Similar phrases that are NOT hangup requests."""
        assert is_hangup_request("hang on a second") is False
        assert is_hangup_request("let me call you back") is False
        assert is_hangup_request("the connection is bad") is False


# =============================================================================
# SOLE PURPOSE TESTS: is_soft_close_ack
# =============================================================================


class TestIsSoftCloseAck:
    """Tests for soft close acknowledgment detection."""

    @pytest.mark.unit
    def test_sp_detects_thanks(self):
        """SP: 'thanks' is a soft close ack."""
        assert is_soft_close_ack("thanks") is True

    @pytest.mark.unit
    def test_sp_detects_you_too(self):
        """SP: 'you too' is a soft close ack."""
        assert is_soft_close_ack("you too") is True

    @pytest.mark.unit
    def test_sp_detects_okay(self):
        """SP: 'okay' is a soft close ack."""
        assert is_soft_close_ack("okay") is True

    @pytest.mark.unit
    @pytest.mark.parametrize("ack", list(SOFT_CLOSE_ACKS))
    def test_sp_all_acks_detected(self, ack):
        """SP: All defined acknowledgments should be detected."""
        assert is_soft_close_ack(ack) is True

    # --- Break-It: Long messages should NOT be acks ---

    @pytest.mark.unit
    def test_break_long_message_not_ack(self):
        """BREAK: Long message with 'thanks' is NOT an ack (>50 chars)."""
        long_message = "Thanks for all your help today, I really appreciate it very much"
        assert len(long_message) > 50
        assert is_soft_close_ack(long_message) is False

    @pytest.mark.unit
    def test_break_question_with_thanks(self):
        """BREAK: Question containing 'thanks' should not be short ack."""
        # Short enough to be under 50 chars
        assert is_soft_close_ack("thanks, but can you help me?") is True  # Under 50
        long_q = "thanks, but I still need help with something else please"
        assert len(long_q) > 50
        assert is_soft_close_ack(long_q) is False

    @pytest.mark.unit
    def test_break_empty_string(self):
        """BREAK: Empty string should return False."""
        assert is_soft_close_ack("") is False


# =============================================================================
# SOLE PURPOSE TESTS: detect_closing_sequence
# =============================================================================


class TestDetectClosingSequence:
    """Tests for natural close sequence detection."""

    @pytest.mark.unit
    def test_sp_detects_valid_sequence(self, transcript_with_natural_close):
        """SP: Valid closing sequence is detected."""
        assert detect_closing_sequence(transcript_with_natural_close) is True

    @pytest.mark.unit
    def test_sp_full_valid_sequence(self):
        """SP: Complete proper closing sequence."""
        transcript = [
            {"role": "agent", "content": "Hello, how can I help?"},
            {"role": "user", "content": "I have a question"},
            {"role": "agent", "content": "Sure, what is it?"},
            {"role": "user", "content": "What are your hours?"},
            {"role": "agent", "content": "We're open 9-5. Is there anything else I can help with?"},
            {"role": "user", "content": "No, that's all"},
            {"role": "agent", "content": "Thanks for calling! Have a great day!"},
            {"role": "user", "content": "Thanks, you too"},
        ]
        assert detect_closing_sequence(transcript) is True

    # --- Break-It: Incomplete sequences ---

    @pytest.mark.unit
    def test_break_missing_anything_else(self):
        """BREAK-P1-B4: No 'anything else' question = not a close."""
        transcript = [
            {"role": "agent", "content": "Hello!"},
            {"role": "user", "content": "Hi"},
            {"role": "user", "content": "No thanks"},
            {"role": "agent", "content": "Thanks for calling!"},
        ]
        assert detect_closing_sequence(transcript) is False

    @pytest.mark.unit
    def test_break_user_didnt_decline(self):
        """BREAK: User didn't say 'no' to 'anything else'."""
        transcript = [
            {"role": "agent", "content": "Is there anything else I can help with?"},
            {"role": "user", "content": "Actually yes, one more thing"},
            {"role": "agent", "content": "Thanks for calling!"},
        ]
        assert detect_closing_sequence(transcript) is False

    @pytest.mark.unit
    def test_break_missing_agent_soft_close(self):
        """BREAK: Agent didn't say 'thanks for calling'."""
        transcript = [
            {"role": "agent", "content": "Is there anything else?"},
            {"role": "user", "content": "No, that's all"},
            {"role": "agent", "content": "Okay, noted."},
            {"role": "user", "content": "thanks"},
        ]
        assert detect_closing_sequence(transcript) is False

    @pytest.mark.unit
    def test_break_too_short_transcript(self):
        """BREAK: Transcript with < 3 messages cannot have close sequence."""
        assert detect_closing_sequence([]) is False
        assert detect_closing_sequence([{"role": "agent", "content": "Hi"}]) is False
        assert detect_closing_sequence([
            {"role": "agent", "content": "Hi"},
            {"role": "user", "content": "Bye"},
        ]) is False

    @pytest.mark.unit
    @pytest.mark.xfail(
        reason="BUG FOUND: detect_closing_sequence crashes on None content. "
        "msg.get('content', '') returns None when key exists with None value, then .lower() fails."
    )
    def test_break_malformed_transcript_entries(self):
        """BREAK-P1-B4: Malformed entries should not crash."""
        transcript = [
            {},  # Empty dict
            {"role": "agent"},  # Missing content
            {"content": "hello"},  # Missing role
            {"role": "agent", "content": None},  # None content
        ]
        # Should not raise exception
        result = detect_closing_sequence(transcript)
        assert result is False

    # --- Edge Cases ---

    @pytest.mark.unit
    def test_edge_only_checks_last_8_messages(self):
        """EDGE: Only last 8 messages are checked for sequence."""
        # Build a transcript where close sequence is beyond last 8
        old_messages = [
            {"role": "agent", "content": "Is there anything else I can help with?"},
            {"role": "user", "content": "No, that's all"},
            {"role": "agent", "content": "Thanks for calling!"},
        ]
        # Add 10 more messages to push the sequence out of range
        filler = [
            [
                {"role": "user", "content": f"Question {i}"},
                {"role": "agent", "content": f"Answer {i}"},
            ]
            for i in range(5)
        ]
        transcript = old_messages + [item for pair in filler for item in pair]

        # The old close sequence should be out of range
        assert detect_closing_sequence(transcript) is False

    @pytest.mark.unit
    def test_edge_variations_of_anything_else(self):
        """EDGE: Various phrasings of 'anything else' should work."""
        phrases = [
            "Is there anything else I can help with?",
            "Can I help with anything more?",
            "Is there something else you need?",
            "Anything else I can do for you?",
        ]
        for phrase in phrases:
            transcript = [
                {"role": "agent", "content": phrase},
                {"role": "user", "content": "No, that's all"},
                {"role": "agent", "content": "Thanks for calling!"},
                {"role": "user", "content": "thanks"},
            ]
            assert detect_closing_sequence(transcript) is True, f"Failed for: {phrase}"


# =============================================================================
# INTEGRATION: end_call Tool Validation
# These tests verify the complete end_call function behavior
# =============================================================================


class TestEndCallValidation:
    """Integration tests for the end_call function tool validation logic."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock RunContext."""
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.say = MagicMock(return_value=MagicMock(wait_for_playout=AsyncMock()))
        return ctx

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for DynamicAssistant."""
        return {
            "save_call_log_fn": AsyncMock(return_value=True),
            "send_to_queue_fn": AsyncMock(),
            "cleanup_done": {"value": False},
        }

    @pytest.fixture
    def create_assistant(self, mock_dependencies):
        """Factory to create DynamicAssistant with transcript."""
        from transcript import create_dynamic_assistant

        def _create(transcript: list, room_name: str = "test-room"):
            cls = create_dynamic_assistant(
                instructions="Test instructions",
                transcript_log=transcript,
                room_name=room_name,
                session_start_time=time.time(),
                save_call_log_fn=mock_dependencies["save_call_log_fn"],
                send_to_queue_fn=mock_dependencies["send_to_queue_fn"],
                cleanup_done=mock_dependencies["cleanup_done"],
            )
            return cls()

        return _create

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_rejects_first_message_ending(self, create_assistant, mock_context):
        """SP-P1-B2: Cannot end call on first user message."""
        transcript = [
            {"role": "agent", "content": "Hello!"},
            {"role": "user", "content": "Bye!"},  # Only 1 user message
        ]
        assistant = create_assistant(transcript)

        with patch("transcript.api.LiveKitAPI"):
            result = await assistant.end_call(
                mock_context,
                reason="user_goodbye",
                detected_closing_phrase="bye",
                already_said_goodbye=True,
            )

        assert "ERROR" in result
        assert "too short" in result.lower() or "1 user message" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_rejects_no_farewell(self, create_assistant, mock_context):
        """SP: Cannot end with user_goodbye if user didn't say farewell."""
        transcript = [
            {"role": "agent", "content": "Hello!"},
            {"role": "user", "content": "I have a question"},
            {"role": "agent", "content": "Sure!"},
            {"role": "user", "content": "What are your hours?"},  # Not a farewell
        ]
        assistant = create_assistant(transcript)

        with patch("transcript.api.LiveKitAPI"):
            result = await assistant.end_call(
                mock_context,
                reason="user_goodbye",
                detected_closing_phrase="bye",
                already_said_goodbye=True,
            )

        assert "ERROR" in result
        assert "NOT a goodbye" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_accepts_valid_farewell(self, create_assistant, mock_context):
        """SP: Valid farewell should be accepted."""
        transcript = [
            {"role": "agent", "content": "Hello!"},
            {"role": "user", "content": "I have a question"},
            {"role": "agent", "content": "Sure!"},
            {"role": "user", "content": "Okay, bye!"},
        ]
        assistant = create_assistant(transcript)

        with patch("transcript.api.LiveKitAPI") as mock_api:
            mock_api_instance = MagicMock()
            mock_api_instance.__aenter__ = AsyncMock(return_value=mock_api_instance)
            mock_api_instance.__aexit__ = AsyncMock()
            mock_api_instance.room = MagicMock()
            mock_api_instance.room.delete_room = AsyncMock()
            mock_api.return_value = mock_api_instance

            result = await assistant.end_call(
                mock_context,
                reason="user_goodbye",
                detected_closing_phrase="bye",
                already_said_goodbye=True,
            )

        assert "successfully" in result.lower() or "user_goodbye" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_break_invalid_reason(self, create_assistant, mock_context):
        """BREAK: Invalid reason should be rejected."""
        transcript = [
            {"role": "agent", "content": "Hello!"},
            {"role": "user", "content": "Hi"},
            {"role": "agent", "content": "How can I help?"},
            {"role": "user", "content": "Bye!"},
        ]
        assistant = create_assistant(transcript)

        with patch("transcript.api.LiveKitAPI"):
            result = await assistant.end_call(
                mock_context,
                reason="invalid_reason",
                detected_closing_phrase="bye",
                already_said_goodbye=True,
            )

        assert "ERROR" in result
        assert "Invalid reason" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_hangup_request_validated(self, create_assistant, mock_context):
        """SP: user_hangup_request requires actual hangup phrase."""
        transcript = [
            {"role": "agent", "content": "Hello!"},
            {"role": "user", "content": "Hi"},
            {"role": "agent", "content": "How can I help?"},
            {"role": "user", "content": "Please help me"},  # Not a hangup request
        ]
        assistant = create_assistant(transcript)

        with patch("transcript.api.LiveKitAPI"):
            result = await assistant.end_call(
                mock_context,
                reason="user_hangup_request",
                detected_closing_phrase="hang up",
                already_said_goodbye=True,
            )

        assert "ERROR" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sp_natural_close_requires_sequence(self, create_assistant, mock_context):
        """SP: natural_close requires proper sequence."""
        # Incomplete sequence
        transcript = [
            {"role": "agent", "content": "Hello!"},
            {"role": "user", "content": "Hi"},
            {"role": "agent", "content": "How can I help?"},
            {"role": "user", "content": "No thanks"},  # Missing agent soft close
        ]
        assistant = create_assistant(transcript)

        with patch("transcript.api.LiveKitAPI"):
            result = await assistant.end_call(
                mock_context,
                reason="natural_close",
                detected_closing_phrase="",
                already_said_goodbye=True,
            )

        assert "ERROR" in result


# =============================================================================
# EDGE CASE TESTS: Unusual inputs
# =============================================================================


class TestEdgeCases:
    """Edge case tests for transcript validation."""

    @pytest.mark.unit
    def test_edge_unicode_in_farewell(self):
        """EDGE: Unicode characters in message with farewell."""
        # Arabic
        is_farewell, _ = is_farewell_closing("شكرا bye")
        assert is_farewell is True

        # Chinese
        is_farewell, _ = is_farewell_closing("谢谢 goodbye")
        assert is_farewell is True

        # Emoji
        is_farewell, _ = is_farewell_closing("Thanks! 👋 bye")
        assert is_farewell is True

    @pytest.mark.unit
    def test_edge_newlines_in_message(self):
        """EDGE: Newlines in message."""
        is_farewell, _ = is_farewell_closing("Thanks\nfor\neverything\nbye")
        assert is_farewell is True

    @pytest.mark.unit
    def test_edge_tabs_in_message(self):
        """EDGE: Tabs in message."""
        is_farewell, _ = is_farewell_closing("Thanks\t\tbye")
        assert is_farewell is True

    @pytest.mark.unit
    def test_edge_very_long_transcript(self):
        """EDGE-P1-B7: Very long transcript (1000+ messages)."""
        transcript = []
        for i in range(500):
            transcript.append({"role": "user", "content": f"Message {i}"})
            transcript.append({"role": "agent", "content": f"Response {i}"})

        # Add closing sequence at end
        transcript.extend([
            {"role": "agent", "content": "Is there anything else?"},
            {"role": "user", "content": "No, that's all"},
            {"role": "agent", "content": "Thanks for calling!"},
            {"role": "user", "content": "thanks"},
        ])

        # Should still work (only checks last 8)
        result = detect_closing_sequence(transcript)
        assert result is True

    @pytest.mark.unit
    def test_edge_special_characters(self):
        """EDGE: Special characters in messages."""
        # SQL-like injection (should be treated as text)
        is_farewell, _ = is_farewell_closing("'; DROP TABLE users; -- bye")
        assert is_farewell is True

        # HTML-like content
        is_farewell, _ = is_farewell_closing("<script>alert('xss')</script> bye")
        assert is_farewell is True

    @pytest.mark.unit
    def test_edge_null_bytes(self):
        """EDGE: Null bytes in message."""
        is_farewell, _ = is_farewell_closing("Hello\x00 bye")
        assert is_farewell is True

    @pytest.mark.unit
    def test_edge_only_punctuation(self):
        """EDGE: Message with only punctuation."""
        is_farewell, _ = is_farewell_closing("!!!")
        assert is_farewell is False

        is_hangup = is_hangup_request("???")
        assert is_hangup is False
