import unittest

from command_guide import (
    category_help_request,
    format_full_guide,
    help_response,
    is_help_request,
)


class CommandGuideTests(unittest.TestCase):
    def test_recognizes_general_and_question_help_requests(self):
        self.assertTrue(is_help_request("list commands"))
        self.assertTrue(is_help_request("help youtube"))
        self.assertTrue(is_help_request("how do I move a video forward"))
        self.assertTrue(is_help_request("detailed help"))
        self.assertTrue(is_help_request("explain forward command"))
        self.assertTrue(is_help_request("what are the WhatsApp commands"))
        self.assertTrue(is_help_request("health calendar"))
        self.assertFalse(is_help_request("search Python tutorial"))

    def test_general_help_is_a_short_overview(self):
        response = help_response("what can you do")
        self.assertIn("YouTube", response)
        self.assertIn("WhatsApp", response)
        self.assertIn("printed the full command guide", response)

    def test_category_help_lists_only_that_category(self):
        response = help_response("help youtube")
        self.assertIn("For YouTube", response)
        self.assertIn("detailed help", response)
        self.assertIn("explain forward command", response)

    def test_explain_forward_returns_only_forward_command_help(self):
        response = help_response("explain forward command", context="youtube")
        self.assertIn("Seek forward", response)
        self.assertIn("forward ten seconds", response)
        self.assertNotIn("Rewind", response)

    def test_specific_video_forward_question_is_not_browser_history(self):
        response = help_response("how do I move a video forward")
        self.assertIn("Seek forward", response)
        self.assertIn("forward ten seconds", response)

    def test_go_back_question_returns_browser_history(self):
        response = help_response("how do I go back")
        self.assertIn("Browser history", response)
        self.assertIn("go back or go forward", response)

    def test_contextual_help_uses_current_mode(self):
        response = help_response("help", context="whatsapp")
        self.assertIn("Whatsapp commands:", response)
        self.assertNotIn("Youtube commands:", response)

    def test_category_help_request_resolves_explicit_and_contextual_help(self):
        self.assertEqual(category_help_request("help youtube"), "youtube")
        self.assertEqual(
            category_help_request("what are the WhatsApp commands"),
            "whatsapp",
        )
        self.assertEqual(
            category_help_request("help", context="youtube"),
            "youtube",
        )
        self.assertIsNone(category_help_request("how do I go back", context="youtube"))

    def test_specific_browser_help_remains_available_inside_youtube(self):
        response = help_response("how do I go back", context="youtube")
        self.assertIn("Browser history", response)

    def test_full_guide_contains_every_category(self):
        guide = format_full_guide()
        for heading in (
            "Youtube commands:",
            "Chrome commands:",
            "Whatsapp commands:",
            "Google commands:",
            "Calendar commands:",
            "Assistant commands:",
        ):
            self.assertIn(heading, guide)


if __name__ == "__main__":
    unittest.main()
