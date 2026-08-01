import unittest
from unittest.mock import Mock, patch

import voice


class VoiceCommandTests(unittest.TestCase):
    def setUp(self):
        # Command-routing tests should not control the developer's live Chrome.
        self.begin_quiet = patch(
            "voice.begin_youtube_quiet_mode", return_value=False
        ).start()
        self.end_quiet = patch("voice.end_youtube_quiet_mode").start()
        self.addCleanup(patch.stopall)

    @patch("voice.listen", side_effect=["next", "stop help"])
    @patch("voice.speak")
    def test_interactive_help_can_stop_after_finding_a_command(self, speak, listen):
        voice.run_interactive_help("youtube")

        self.assertEqual(listen.call_count, 2)
        speak.assert_any_call("Leaving command help.")

    @patch("voice.speak")
    def test_quit_assistant_works_from_main_dispatcher(self, speak):
        with self.assertRaises(SystemExit):
            voice.execute("quit assistant")

        speak.assert_called_once_with("Goodbye!")

    @patch("voice.speak")
    @patch("voice.listen", return_value="quit assistant")
    def test_quit_assistant_works_inside_google_mode(self, _listen, speak):
        with self.assertRaises(SystemExit):
            voice.execute_google()

        speak.assert_any_call("Goodbye!")

    @patch("voice.time.sleep")
    @patch("voice.provide_command_help")
    @patch("voice.speak")
    @patch("voice.listen", return_value="help")
    def test_help_inside_youtube_uses_youtube_context(
        self, _listen, _speak, provide_help, _sleep
    ):
        voice.execute_yt()

        provide_help.assert_called_once_with("help", context="youtube")

    @patch("voice.run_interactive_help")
    def test_detailed_help_starts_interactive_youtube_guide(self, interactive_help):
        voice.provide_command_help("detailed help", context="youtube")

        interactive_help.assert_called_once_with("youtube")

    def test_extracts_inline_youtube_query(self):
        self.assertEqual(
            voice.get_youtube_search_query("search Java OOPS concepts"),
            "java oops concepts",
        )
        self.assertEqual(
            voice.get_youtube_search_query("search for Python tutorials"),
            "python tutorials",
        )
        self.assertEqual(voice.get_youtube_search_query("search"), "")
        self.assertEqual(
            voice.get_youtube_search_query("search Python tutorial in a new window"),
            "python tutorial",
        )

    def test_extracts_inline_google_query(self):
        self.assertEqual(
            voice.get_google_search_query("search Google for Java collections"),
            "java collections",
        )
        self.assertEqual(voice.get_google_search_query("search"), "")
        self.assertEqual(
            voice.get_google_search_query("search Java in a new tab"),
            "java",
        )

    @patch("voice.time.sleep")
    @patch("voice.open_in_chrome")
    @patch("voice.speak")
    @patch("voice.listen", return_value="search java collections")
    def test_google_search_uses_results_url_without_screen_coordinates(
        self, _listen, speak, open_in_chrome, _sleep
    ):
        voice.execute_google()

        open_in_chrome.assert_called_once_with(
            "https://www.google.com/search?q=java+collections",
            "same_tab",
        )
        speak.assert_any_call("Searching Google for java collections")

    @patch("voice.time.sleep")
    @patch("voice.open_in_chrome")
    @patch("voice.speak")
    @patch("voice.listen", side_effect=["search", "python decorators"])
    def test_google_search_prompts_when_query_is_missing(
        self, _listen, speak, open_in_chrome, _sleep
    ):
        voice.execute_google()

        open_in_chrome.assert_called_once_with(
            "https://www.google.com/search?q=python+decorators",
            "same_tab",
        )
        speak.assert_any_call("What should I search Google for?")

    def test_calendar_event_title_and_url_are_encoded(self):
        title = voice.get_calendar_event_title(
            "create calendar event Cognizant interview"
        )

        self.assertEqual(title, "cognizant interview")
        self.assertEqual(
            voice.build_calendar_event_url(title, voice.date(2026, 8, 3)),
            "https://calendar.google.com/calendar/render?"
            "action=TEMPLATE&text=cognizant+interview&"
            "dates=20260803%2F20260804",
        )

    def test_spoken_calendar_date_is_required_and_parsed(self):
        reference = voice.date(2026, 8, 1)

        self.assertEqual(
            voice.parse_spoken_date("3 August 2026", today=reference),
            voice.date(2026, 8, 3),
        )
        self.assertEqual(
            voice.parse_spoken_date("tomorrow", today=reference),
            voice.date(2026, 8, 2),
        )
        self.assertIsNone(voice.parse_spoken_date("sometime", today=reference))

    @patch("voice.time.sleep")
    @patch("voice.open_in_chrome")
    @patch("voice.speak")
    @patch(
        "voice.listen",
        side_effect=["create event cognizant interview", "3 august 2026"],
    )
    def test_calendar_opens_reviewable_draft_without_screen_coordinates(
        self, _listen, speak, open_in_chrome, _sleep
    ):
        voice.execute_reminder()

        open_in_chrome.assert_called_once_with(
            "https://calendar.google.com/calendar/render?"
            "action=TEMPLATE&text=cognizant+interview&"
            "dates=20260803%2F20260804",
            "same_tab",
        )
        speak.assert_any_call("Review the event details, then save it in Calendar.")

    @patch("voice.time.sleep")
    @patch("voice.provide_command_help")
    @patch("voice.speak")
    @patch("voice.listen", return_value="health calendar")
    def test_calendar_help_accepts_common_health_misrecognition(
        self, _listen, _speak, provide_help, _sleep
    ):
        voice.execute_reminder()

        provide_help.assert_called_once_with("health calendar", context="calendar")

    @patch("voice.execute_reminder", return_value="exit")
    @patch("voice.open_in_chrome")
    @patch("voice.speak")
    def test_open_google_calendar_routes_to_calendar_not_google(
        self, _speak, open_in_chrome, execute_reminder
    ):
        voice.execute("open google calendar")

        open_in_chrome.assert_called_once_with(
            "https://calendar.google.com", "same_tab"
        )
        execute_reminder.assert_called_once_with()

    @patch("voice.time.sleep")
    @patch("voice.exit_chrome_mode", return_value="exit")
    @patch("voice.speak")
    @patch("voice.listen", return_value="exit calendar")
    def test_calendar_exit_uses_tab_confirmation(
        self, _listen, _speak, exit_mode, _sleep
    ):
        self.assertEqual(voice.execute_reminder(), "exit")
        exit_mode.assert_called_once_with("Calendar")

    @patch("voice.time.sleep")
    @patch("voice.save_calendar_draft", return_value=True)
    @patch("voice.speak")
    @patch("voice.listen", return_value="save it")
    def test_calendar_save_command_uses_confirmed_save_flow(
        self, _listen, _speak, save_draft, _sleep
    ):
        voice.execute_reminder()

        save_draft.assert_called_once_with()

    @patch("voice.time.sleep")
    @patch("voice.exit_chrome_mode", return_value="exit")
    @patch("voice.speak")
    @patch("voice.listen", return_value="leave calendar mode")
    def test_leave_calendar_mode_alias_exits(self, _listen, _speak, exit_mode, _sleep):
        self.assertEqual(voice.execute_reminder(), "exit")
        exit_mode.assert_called_once_with("Calendar")

    @patch("voice.time.sleep")
    @patch("voice.speak")
    @patch("voice.click_by_title", return_value=True)
    @patch("voice.activate_chrome")
    @patch("voice.listen_for_short_response", return_value="yes please")
    @patch(
        "voice.get_active_chrome_url",
        side_effect=[
            "https://calendar.google.com/calendar/u/0/r/eventedit",
            "https://calendar.google.com/calendar/u/0/r",
        ],
    )
    def test_calendar_save_click_is_confirmed_and_verified_cautiously(
        self, _url, listen_short, activate, click_title, speak, _sleep
    ):
        self.assertTrue(voice.save_calendar_draft())

        listen_short.assert_called_once_with(
            ready_prompt="Save this Calendar event? Say yes or no."
        )
        activate.assert_called_once_with()
        click_title.assert_called_once_with("save", ignore_header=False)
        speak.assert_any_call(
            "Calendar accepted the Save command. Please verify the event."
        )

    @patch("voice.time.sleep")
    @patch("voice.open_in_chrome")
    @patch("voice.speak")
    @patch("voice.listen", return_value="search java oops concepts")
    def test_inline_youtube_search_opens_results_url(
        self, _listen, speak, open_in_chrome, _sleep
    ):
        voice.execute_yt()

        open_in_chrome.assert_called_once_with(
            "https://www.youtube.com/results?search_query=java+oops+concepts"
        )
        speak.assert_any_call("Searching YouTube for java oops concepts")

    @patch("voice.time.sleep")
    @patch("voice.open_in_chrome")
    @patch("voice.speak")
    @patch("voice.listen", side_effect=["search", "", "python tutorial"])
    def test_separate_query_retries_after_unclear_speech(
        self, _listen, speak, open_in_chrome, _sleep
    ):
        voice.execute_yt()

        open_in_chrome.assert_called_once_with(
            "https://www.youtube.com/results?search_query=python+tutorial"
        )
        speak.assert_any_call("Please say the search query again.")

    @patch("voice.time.sleep")
    @patch("voice.speak")
    @patch("voice.send_key_to_chrome", return_value=(True, ""))
    @patch("voice.listen", return_value="scroll down")
    def test_scroll_targets_chrome_with_macos_page_down(
        self, _listen, send_key, speak, _sleep
    ):
        with patch.object(voice, "IS_MACOS", True):
            voice.execute_yt()

        send_key.assert_called_once_with(121)
        speak.assert_any_call("Page down command accepted by Chrome")

    @patch("voice.time.sleep")
    @patch("voice.click_by_title")
    @patch("voice.activate_chrome")
    @patch("voice.speak")
    @patch("voice.listen", return_value="open oop 1 introduction")
    def test_inline_open_clicks_matching_visible_title(
        self, _listen, speak, activate_chrome, click_by_title, _sleep
    ):
        voice.execute_yt()

        activate_chrome.assert_called_once_with()
        click_by_title.assert_called_once_with("oop 1 introduction")
        speak.assert_any_call("Looking for oop 1 introduction")

    @patch("voice.time.sleep")
    @patch("voice.pyautogui.press")
    @patch("voice.activate_chrome")
    @patch("voice.speak")
    @patch("voice.listen", return_value="forward")
    def test_plain_forward_seeks_video_not_browser_history(
        self, _listen, speak, activate_chrome, press, _sleep
    ):
        voice.execute_yt()

        activate_chrome.assert_called_once_with()
        press.assert_called_once_with("right", presses=2, interval=0.1)
        speak.assert_any_call("Moving the video forward ten seconds")

    @patch("voice.time.sleep")
    @patch("voice.speak")
    @patch("voice.listen", return_value="open whatsapp")
    def test_open_whatsapp_leaves_youtube_mode(self, _listen, speak, _sleep):
        self.assertEqual(voice.execute_yt(), "open whatsapp")

        speak.assert_any_call("Leaving YouTube and switching to WhatsApp")

    @patch("voice.time.sleep")
    @patch("voice.speak")
    @patch("voice.ask_to_close_active_tab", return_value=False)
    @patch("voice.pause_youtube_video_if_playing")
    @patch("voice.listen", return_value="exit")
    def test_exit_leaves_youtube_mode(
        self, _listen, pause_video, ask_to_close, speak, _sleep
    ):
        self.assertEqual(voice.execute_yt(), "exit")

        pause_video.assert_called_once_with()
        ask_to_close.assert_called_once_with("YouTube")
        speak.assert_any_call("Exiting YouTube command mode.")

    @patch("voice.speak")
    @patch("voice.change_chrome_history", return_value=True)
    def test_go_back_uses_verified_chrome_history(self, change_history, speak):
        with patch.object(voice, "IS_MACOS", True):
            self.assertTrue(voice.handle_chrome_navigation("go back"))

        change_history.assert_called_once_with("back")
        speak.assert_called_once_with("Went back to the previous page")

    @patch("voice.speak")
    @patch("voice.run_chrome_applescript", return_value=(True, ""))
    def test_reload_reports_only_accepted_chrome_command(self, run_script, speak):
        with patch.object(voice, "IS_MACOS", True):
            self.assertTrue(voice.handle_chrome_navigation("reload"))

        run_script.assert_called_once()
        speak.assert_called_once_with("Reload command accepted by Chrome")

    @patch("voice.speak")
    @patch("voice.run_chrome_applescript", return_value=(True, ""))
    def test_maximize_window_is_shared_chrome_navigation(self, run_script, speak):
        with patch.object(voice, "IS_MACOS", True):
            self.assertTrue(voice.handle_chrome_navigation("maximize window"))

        run_script.assert_called_once()
        speak.assert_called_once_with("Chrome window maximized")

    @patch("voice.speak")
    @patch("voice.pyautogui.press")
    @patch("voice.activate_chrome")
    def test_dismiss_popup_presses_escape(self, activate, press, speak):
        self.assertTrue(voice.handle_chrome_navigation("dismiss popup"))

        activate.assert_called_once_with()
        press.assert_called_once_with("esc")
        speak.assert_called_once_with("Pressed Escape to dismiss the popup")

    @patch("voice.pyautogui.write")
    @patch("voice.listen")
    @patch("voice.speak")
    @patch("voice.wait_for_whatsapp_ready", return_value=False)
    def test_whatsapp_does_nothing_before_chats_are_ready(
        self, _ready, speak, listen, write
    ):
        self.assertEqual(voice.whatsapp_execute_safe(), "exit")

        listen.assert_not_called()
        write.assert_not_called()
        speak.assert_called_once_with(
            "WhatsApp did not finish loading, so I will not type or send anything."
        )

    @patch("voice.speak")
    @patch("voice.fuzz.token_set_ratio", return_value=95)
    @patch("voice.read_ocr")
    @patch("voice.pyautogui.click")
    @patch("voice.pyautogui.moveTo")
    @patch("voice.get_chrome_bounds", return_value=(0, 0, 1000, 500))
    @patch("voice.pyautogui.screenshot")
    def test_ocr_click_scales_retina_coordinates(
        self,
        screenshot,
        _bounds,
        move_to,
        click,
        read_ocr,
        _score,
        _speak,
    ):
        captured_image = Mock()
        captured_image.size = (2000, 1000)
        screenshot.return_value = captured_image
        read_ocr.return_value = [
            # Search bar: high fuzzy score but excluded as browser chrome/header.
            (
                [(400, 40), (600, 40), (600, 100), (400, 100)],
                "merge sort",
                0.99,
            ),
            # Video title: covers more requested words and should win.
            (
                [(400, 200), (600, 200), (600, 300), (400, 300)],
                "Merge Sort Algorithm Recursion",
                0.98,
            ),
            # Channel name alone must not beat the fuller title.
            (
                [(400, 320), (600, 320), (600, 360), (400, 360)],
                "Abdul Bari",
                0.99,
            ),
        ]

        voice.click_by_title("merge sort algorithm by abdul bari")

        move_to.assert_called_once_with(250, 125)
        click.assert_called_once_with()

    @patch("voice.subprocess.run")
    def test_macos_speech_uses_native_say(self, run):
        with patch.object(voice, "IS_MACOS", True):
            voice.speak("Test message")

        run.assert_called_once_with(["/usr/bin/say", "Test message"], check=False)

    @patch("voice.subprocess.run")
    def test_macos_speech_smooths_multiline_help(self, run):
        with patch.object(voice, "IS_MACOS", True):
            voice.speak("Calendar commands:\n- create event\n- save it")

        run.assert_called_once_with(
            [
                "/usr/bin/say",
                "Calendar commands: - create event - save it",
            ],
            check=False,
        )


class YouTubeQuietModeTests(unittest.TestCase):
    @patch("voice.time.sleep")
    @patch("voice.pyautogui.press")
    @patch("voice.activate_chrome")
    @patch("voice.get_active_chrome_url", return_value="https://youtube.com/watch?v=1")
    def test_video_is_muted_during_command_and_restored_afterward(
        self, _url, activate, press, _sleep
    ):
        with (
            patch.object(voice, "youtube_muted_by_user", False),
            patch.object(voice, "youtube_temporarily_muted", False),
        ):
            self.assertTrue(voice.begin_youtube_quiet_mode())
            voice.end_youtube_quiet_mode()

        self.assertEqual(
            press.call_args_list, [unittest.mock.call("m"), unittest.mock.call("m")]
        )
        self.assertEqual(activate.call_count, 2)

    @patch("voice.pyautogui.press")
    @patch("voice.activate_chrome")
    @patch("voice.get_active_chrome_url", return_value="https://youtube.com/watch?v=1")
    def test_user_muted_video_is_not_temporarily_unmuted(self, _url, activate, press):
        with (
            patch.object(voice, "youtube_muted_by_user", True),
            patch.object(voice, "youtube_temporarily_muted", False),
        ):
            self.assertFalse(voice.begin_youtube_quiet_mode())
            voice.end_youtube_quiet_mode()

        press.assert_not_called()
        activate.assert_not_called()


class ChromeTabBehaviorTests(unittest.TestCase):
    def test_same_tab_is_default_and_explicit_targets_are_detected(self):
        self.assertEqual(
            voice.chrome_disposition_from_command("open youtube"), "same_tab"
        )
        self.assertEqual(
            voice.chrome_disposition_from_command("open youtube in a new tab"),
            "new_tab",
        )
        self.assertEqual(
            voice.chrome_disposition_from_command("open youtube in a new window"),
            "new_window",
        )

    @patch("voice.time.sleep")
    @patch("voice.subprocess.run")
    def test_open_in_chrome_reuses_active_tab_by_default(self, run, _sleep):
        run.return_value.returncode = 0
        run.return_value.stderr = ""

        with patch.object(voice, "IS_MACOS", True):
            voice.open_in_chrome("https://www.youtube.com")

        script = run.call_args.args[0][2]
        self.assertIn("set URL of active tab of front window", script)
        self.assertNotIn("make new tab at end", script)

    @patch("voice.time.sleep")
    @patch("voice.subprocess.run")
    def test_open_in_chrome_can_create_explicit_new_window(self, run, _sleep):
        run.return_value.returncode = 0
        run.return_value.stderr = ""

        with patch.object(voice, "IS_MACOS", True):
            voice.open_in_chrome("https://www.youtube.com", disposition="new_window")

        script = run.call_args.args[0][2]
        self.assertIn("make new window", script)

    @patch("voice.listen", side_effect=["", "yes"])
    @patch("voice.speak")
    def test_short_confirmation_announces_ready_and_retries(self, speak, listen):
        self.assertEqual(voice.listen_for_short_response(), "yes")

        self.assertEqual(listen.call_count, 2)
        self.assertEqual(speak.call_args_list[0], unittest.mock.call("Ready"))
        speak.assert_any_call(
            "I did not hear that. Please answer once more after Ready."
        )

    @patch("voice.listen", return_value="yes")
    @patch("voice.speak")
    def test_close_tab_confirmation_repeats_specific_question(self, speak, _listen):
        self.assertTrue(voice.ask_to_close_active_tab("YouTube"))

        self.assertEqual(
            speak.call_args_list,
            [
                unittest.mock.call("Close the YouTube tab? Say yes or no."),
                unittest.mock.call("Ready"),
            ],
        )

    @patch("voice.speak")
    @patch("voice.run_chrome_applescript", return_value=(True, "paused"))
    @patch("voice.get_active_chrome_url", return_value="https://youtube.com/watch?v=1")
    def test_running_youtube_video_is_paused_before_exit(self, _url, run_script, speak):
        self.assertTrue(voice.pause_youtube_video_if_playing())

        self.assertIn("video.pause()", run_script.call_args.args[0])
        speak.assert_called_once_with("Paused the YouTube video before leaving.")

    @patch("voice.speak")
    @patch("voice.run_chrome_applescript", return_value=(True, "already-paused"))
    @patch("voice.get_active_chrome_url", return_value="https://youtube.com/watch?v=1")
    def test_paused_youtube_video_is_not_toggled_on_exit(self, _url, _run, speak):
        self.assertTrue(voice.pause_youtube_video_if_playing())

        speak.assert_not_called()

    @patch("voice.close_active_chrome_tab", return_value=True)
    @patch("voice.ask_to_close_active_tab", return_value=True)
    @patch("voice.speak")
    def test_exiting_chrome_mode_closes_only_after_yes(self, speak, ask, close):
        self.assertEqual(voice.exit_chrome_mode("WhatsApp"), "exit")

        ask.assert_called_once_with("WhatsApp")
        close.assert_called_once_with()
        speak.assert_any_call("Closed the WhatsApp tab.")

    @patch("voice.close_active_chrome_tab")
    @patch("voice.ask_to_close_active_tab", return_value=False)
    @patch("voice.speak")
    def test_exiting_chrome_mode_leaves_tab_open_after_no(self, speak, _ask, close):
        self.assertEqual(voice.exit_chrome_mode("Google"), "exit")

        close.assert_not_called()
        speak.assert_any_call("Leaving the Google tab open.")


class WhatsAppContactTests(unittest.TestCase):
    def test_confirmed_whatsapp_message_runs_safe_send_path(self):
        with (
            patch("voice.wait_for_whatsapp_ready", return_value=True),
            patch("voice.get_confirmed_whatsapp_contact", return_value="sonu"),
            patch("voice.click_by_title", return_value=True),
            patch("voice.chrome_text_is_visible", side_effect=[True, True]),
            patch("voice.focus_whatsapp_message_field", return_value=True),
            patch("voice.listen", side_effect=["text hello", "yes", "exit whatsapp"]),
            patch("voice.exit_chrome_mode", return_value="exit"),
            patch("voice.pyautogui.write") as write,
            patch("voice.pyautogui.press") as press,
            patch("voice.pyautogui.hotkey"),
            patch("voice.activate_chrome"),
            patch("voice.time.sleep"),
            patch("voice.speak"),
        ):
            result = voice.whatsapp_execute_safe()

        self.assertEqual(result, "exit")
        self.assertEqual(
            write.call_args_list,
            [
                unittest.mock.call("sonu", interval=0.04),
                unittest.mock.call("hello", interval=0.04),
            ],
        )
        self.assertEqual(
            [
                call
                for call in press.call_args_list
                if call == unittest.mock.call("enter")
            ],
            [unittest.mock.call("enter"), unittest.mock.call("enter")],
        )

    @patch("voice.speak")
    @patch(
        "voice.listen",
        side_effect=["anugra hit", "change contact to anugrahit", "yes"],
    )
    def test_contact_can_be_corrected_before_search(self, listen, speak):
        self.assertEqual(voice.get_confirmed_whatsapp_contact(), "anugrahit")

        self.assertEqual(listen.call_count, 3)
        speak.assert_any_call(
            "I heard anugrahit. Say yes to use it, change contact to followed "
            "by the name, or spell contact."
        )

    @patch("voice.speak")
    @patch(
        "voice.listen",
        side_effect=["wrong name", "spell contact", "a n u space s h", "yes"],
    )
    def test_contact_can_be_spelled(self, _listen, _speak):
        self.assertEqual(voice.get_confirmed_whatsapp_contact(), "anu sh")

    @patch("voice.speak")
    @patch("voice.listen", side_effect=["spell contact", "a n u g r a h a t", "yes"])
    def test_contact_can_request_spelling_immediately(self, _listen, _speak):
        self.assertEqual(voice.get_confirmed_whatsapp_contact(), "anugrahat")

    def test_spelled_contact_normalization(self):
        self.assertEqual(voice.normalize_spelled_contact("r i y a"), "riya")
        self.assertEqual(voice.normalize_spelled_contact("a n u space s h"), "anu sh")


if __name__ == "__main__":
    unittest.main()
