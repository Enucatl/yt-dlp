#!/usr/bin/env python3

import unittest
from unittest.mock import PropertyMock, patch

from test.helper import FakeYDL
from yt_dlp.extractor.reddit import RedditIE


class TestRedditIE(unittest.TestCase):
    def test_gallery_images_accept_images(self) -> None:
        ie = RedditIE(FakeYDL())
        ie._download_json = lambda *args, **kwargs: [{
            'data': {'children': [{'data': {
                'url': 'https://www.reddit.com/r/test/comments/abc123/test/',
                'is_gallery': True,
                'media_metadata': {
                    'image': {'id': 'image', 'e': 'Image', 'm': 'image/png', 's': {'x': 1, 'y': 1}},
                },
            }}]},
        }]
        with patch.object(RedditIE, '_is_logged_in', new_callable=PropertyMock, return_value=True):
            result = ie._real_extract('https://www.reddit.com/r/test/comments/abc123/test/')

        image_format = result['formats'][0]
        self.assertEqual(image_format['url'], 'https://i.redd.it/image.png')
        self.assertEqual(image_format['http_headers']['Accept'], 'image/*')


if __name__ == '__main__':
    unittest.main()
