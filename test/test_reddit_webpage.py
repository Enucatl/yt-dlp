#!/usr/bin/env python3

import unittest
from unittest.mock import patch

from test.helper import FakeYDL
from yt_dlp.extractor.reddit import RedditIE
from yt_dlp.utils import ExtractorError


class TestRedditWebpage(unittest.TestCase):
    URL = 'https://www.reddit.com/r/China/comments/1xhr82t/'

    def setUp(self):
        self.ie = RedditIE(FakeYDL())

    def test_javascript_challenge(self):
        challenge = '''
            <script>await(async e=>e+e)("5650ab7f58e74498")</script>
            <form hidden method="GET">
              <input type="hidden" name="solution">
              <input type="hidden" name="js_challenge" value="1">
              <input type="hidden" name="jsc_token" value="test-token">
            </form>
        '''
        with patch.object(self.ie, '_download_webpage', side_effect=[challenge, 'post HTML']) as download:
            self.assertEqual(self.ie._download_reddit_webpage(self.URL, '1xhr82t'), 'post HTML')
        self.assertEqual(download.call_args.kwargs['query'], {
            'solution': '5650ab7f58e744985650ab7f58e74498',
            'js_challenge': '1',
            'jsc_token': 'test-token',
        })
        self.assertTrue(all(call.kwargs['impersonate'] for call in download.call_args_list))

    def test_unsupported_challenge(self):
        with patch.object(self.ie, '_download_webpage', return_value='<input name="js_challenge">'):
            with self.assertRaisesRegex(ExtractorError, 'unsupported JavaScript challenge'):
                self.ie._download_reddit_webpage(self.URL, '1xhr82t')

    def test_canonical_redirect(self):
        canonical = self.URL + 'mbappe_face_being_removed_or_covered_all_across/'
        shell = f'<div id="canonical-url-updater" value="{canonical}"></div>'
        with patch.object(self.ie, '_download_webpage', side_effect=[shell, 'post HTML']) as download:
            self.assertEqual(self.ie._download_reddit_webpage(self.URL, '1xhr82t'), 'post HTML')
        self.assertEqual(download.call_args.args[0], canonical)

    def test_canonical_redirect_must_match_post(self):
        for canonical in ('https://example.com/', 'https://www.reddit.com/comments/different/'):
            shell = f'<div id="canonical-url-updater" value="{canonical}"></div>'
            with self.subTest(canonical=canonical):
                with patch.object(self.ie, '_download_webpage', return_value=shell) as download:
                    self.assertEqual(self.ie._download_reddit_webpage(self.URL, '1xhr82t'), shell)
                download.assert_called_once()

    def test_block_page_is_not_login_requirement(self):
        with patch.object(self.ie, '_download_reddit_webpage', return_value="You've been blocked by network security"):
            with self.assertRaisesRegex(ExtractorError, 'access may be blocked') as error:
                self.ie._extract_webpage(self.URL, '1xhr82t')
        self.assertTrue(error.exception.expected)


if __name__ == '__main__':
    unittest.main()
