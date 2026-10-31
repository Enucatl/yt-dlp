#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, PropertyMock, patch

from test.helper import FakeYDL
from yt_dlp.extractor.reddit import RedditIE


class TestRedditIE(unittest.TestCase):
    def setUp(self) -> None:
        self.ie = RedditIE(FakeYDL())
        self.ie._download_reddit_webpage = Mock()

    def test_webpage_single_image(self) -> None:
        self.ie._download_reddit_webpage.return_value = '''
            <shreddit-post id="t3_1rpni97" post-type="image"
                content-href="https://i.redd.it/8pwts24oc5og1.jpeg"
                post-title="[OC] Midnight in Alaska." author="takebreaks" subreddit-name="pics"
                created-timestamp="2026-03-10T04:38:18.849000+0000">
                <div slot="post-media-container">
                    <img id="post-image" src="https://preview.redd.it/8pwts24oc5og1.jpeg?width=640&amp;auto=webp">
                </div>
            </shreddit-post>'''

        result = self.ie._extract_webpage('https://www.reddit.com/comments/1rpni97/', '1rpni97')

        self.assertEqual(result['url'], 'https://i.redd.it/8pwts24oc5og1.jpeg')
        self.assertEqual(result['id'], '8pwts24oc5og1')
        self.assertEqual(result['display_id'], '1rpni97')
        self.assertEqual(result['title'], '[OC] Midnight in Alaska.')
        self.assertEqual(result['uploader'], 'takebreaks')
        self.assertEqual(result['channel_id'], 'pics')
        self.assertEqual(result['http_headers']['Accept'], 'image/*')
        self.assertEqual(result['thumbnails'][0]['url'],
                         'https://preview.redd.it/8pwts24oc5og1.jpeg?width=640&auto=webp')

    def test_webpage_gallery_order_and_media_scope(self) -> None:
        self.ie._download_reddit_webpage.return_value = '''
            <shreddit-post id="t3_ad" post-type="image" post-promoted>
                <img src="https://i.redd.it/ad.jpg">
            </shreddit-post>
            <shreddit-post id="t3_1rkxq31" post-type="gallery" gallery
                content-href="https://www.reddit.com/gallery/1rkxq31"
                post-title="My son, 7 years, loves to draw avengers!">
                <img src="https://i.redd.it/avatar.png">
                <div slot="post-media-container">
                    <gallery-carousel post-id="t3_1rkxq31">
                        <ul>
                            <li slot="page-1">
                                <img src="https://preview.redd.it/8x80503eg3ng1.jpg?width=640">
                                <img class="media-lightbox-img" src="https://i.redd.it/8x80503eg3ng1.jpg">
                                <img class="media-lightbox-img" src="https://i.redd.it/8x80503eg3ng1.jpg">
                            </li>
                            <li slot="page-2">
                                <img data-lazy-src="https://preview.redd.it/da0jzz2eg3ng1.jpg?width=640">
                                <img class="media-lightbox-img" src="https://i.redd.it/da0jzz2eg3ng1.jpg">
                            </li>
                        </ul>
                    </gallery-carousel>
                </div>
            </shreddit-post>
            <shreddit-comment><img src="https://i.redd.it/comment.jpg"></shreddit-comment>'''

        result = self.ie._extract_webpage('https://www.reddit.com/comments/1rkxq31/', '1rkxq31')

        entries = list(result['entries'])
        self.assertEqual([entry['id'] for entry in entries], ['8x80503eg3ng1', 'da0jzz2eg3ng1'])
        self.assertEqual([entry['formats'][0]['url'] for entry in entries], [
            'https://i.redd.it/8x80503eg3ng1.jpg',
            'https://i.redd.it/da0jzz2eg3ng1.jpg',
        ])

    def test_webpage_animated_image(self) -> None:
        self.ie._download_reddit_webpage.return_value = '''
            <shreddit-post id="t3_1tii2iv" post-type="gif" post-title="this is not a GIF"
                content-href="https://i.redd.it/pdpodfn2w92h1.gif">
                <div slot="post-media-container">
                    <shreddit-player post-id="t3_1tii2iv" gif
                        src="https://preview.redd.it/pdpodfn2w92h1.gif?width=498&amp;format=mp4&amp;s=signature">
                    </shreddit-player>
                </div>
            </shreddit-post>'''

        result = self.ie._extract_webpage('https://www.reddit.com/comments/1tii2iv/', '1tii2iv')

        self.assertEqual(result['formats'][0]['url'],
                         'https://preview.redd.it/pdpodfn2w92h1.gif?width=498&format=mp4&s=signature')
        self.assertEqual(result['formats'][0]['ext'], 'mp4')
        self.assertEqual(result['id'], 'pdpodfn2w92h1')

    def test_webpage_video_preserves_audio_and_subtitles(self) -> None:
        self.ie._download_reddit_webpage.return_value = '''
            <shreddit-post id="t3_1cl9h0u" post-type="video"
                content-href="https://v.redd.it/a2mdj5d57qyc1"
                post-title="The insurance claim will be interesting">
                <div slot="post-media-container">
                    <shreddit-player post-id="t3_1cl9h0u"
                        src="https://v.redd.it/a2mdj5d57qyc1/HLSPlaylist.m3u8?f=sd%2CsubsAll&amp;v=1"
                        packaged-media-json="{&quot;playbackMp4s&quot;:{&quot;duration&quot;:53}}">
                    </shreddit-player>
                </div>
            </shreddit-post>
            <shreddit-player post-promoted src="https://v.redd.it/ad/HLSPlaylist.m3u8"></shreddit-player>'''
        hls_formats = [
            {'format_id': 'hls-video', 'url': 'https://v.redd.it/a2mdj5d57qyc1/video.m3u8', 'acodec': 'none'},
            {'format_id': 'hls-audio', 'url': 'https://v.redd.it/a2mdj5d57qyc1/audio.m3u8', 'vcodec': 'none'},
        ]
        subtitles = {'en': [{'url': 'https://v.redd.it/a2mdj5d57qyc1/wh_ben_en.vtt'}]}
        self.ie._extract_m3u8_formats_and_subtitles = Mock(return_value=(hls_formats, subtitles))
        self.ie._extract_mpd_formats_and_subtitles = Mock(return_value=([], {}))

        result = self.ie._extract_webpage('https://www.reddit.com/comments/1cl9h0u/', '1cl9h0u')

        self.assertTrue(all(fmt in result['formats'] for fmt in hls_formats))
        self.assertEqual(result['subtitles'], subtitles)
        self.assertEqual(result['id'], 'a2mdj5d57qyc1')
        self.assertEqual(result['duration'], 53)
        self.ie._extract_m3u8_formats_and_subtitles.assert_called_once()
        self.assertIn('https://v.redd.it/a2mdj5d57qyc1/HLSPlaylist.m3u8',
                      self.ie._extract_m3u8_formats_and_subtitles.call_args.args[0])

    def test_webpage_crosspost_retains_wrapper_metadata(self) -> None:
        self.ie._download_reddit_webpage.return_value = '''
            <shreddit-post id="t3_zjjw82" post-type="crosspost" is-crosspost
                content-href="/r/shitposting/comments/ziyepo/cringe/" post-title="Cringe"
                author="Otaku-senpai69420" subreddit-name="dumbfuckers_club">
                <div slot="post-media-container">
                    <shreddit-player post-id="t3_zjjw82"
                        src="https://v.redd.it/a1oneun6pa5a1/HLSPlaylist.m3u8"
                        post-title="Original title" post-author="Original author">
                    </shreddit-player>
                </div>
            </shreddit-post>'''
        self.ie._extract_m3u8_formats_and_subtitles = Mock(return_value=([
            {'url': 'https://v.redd.it/a1oneun6pa5a1/video.m3u8'},
        ], {'en': [{'url': 'https://v.redd.it/a1oneun6pa5a1/captions.vtt'}]}))
        self.ie._extract_mpd_formats_and_subtitles = Mock(return_value=([], {}))

        result = self.ie._extract_webpage('https://www.reddit.com/comments/zjjw82/', 'zjjw82')

        self.assertEqual(result['id'], 'a1oneun6pa5a1')
        self.assertEqual(result['display_id'], 'zjjw82')
        self.assertEqual(result['title'], 'Cringe')
        self.assertEqual(result['uploader'], 'Otaku-senpai69420')
        self.assertEqual(result['channel_id'], 'dumbfuckers_club')

    def test_webpage_text_post_retains_multiple_videos(self) -> None:
        self.ie._download_reddit_webpage.return_value = '''
            <shreddit-post id="t3_wzqkxp" post-type="text"
                content-href="https://www.reddit.com/r/KamenRider/comments/wzqkxp/"
                post-title="Two embedded videos">
                <div slot="text-body">
                    <shreddit-player src="https://v.redd.it/first/HLSPlaylist.m3u8"></shreddit-player>
                    <shreddit-player src="https://v.redd.it/second/HLSPlaylist.m3u8"></shreddit-player>
                </div>
            </shreddit-post>'''
        self.ie._extract_m3u8_formats = Mock(side_effect=lambda url, *args, **kwargs: [{'url': url}])
        self.ie._extract_mpd_formats = Mock(return_value=[])

        result = self.ie._extract_webpage('https://www.reddit.com/comments/wzqkxp/', 'wzqkxp')

        entries = list(result['entries'])
        self.assertEqual([entry['id'] for entry in entries], ['first', 'second'])
        self.assertEqual([entry['formats'][0]['url'] for entry in entries], [
            'https://v.redd.it/first/HLSPlaylist.m3u8',
            'https://v.redd.it/second/HLSPlaylist.m3u8',
        ])

    def test_webpage_external_video_delegation(self) -> None:
        self.ie._download_reddit_webpage.return_value = '''
            <shreddit-post id="t3_6t75wq" post-type="link" is-link-post
                content-href="https://youtu.be/4arBraMyp0Q"
                post-title="Southern man tries to speak without an accent" author="MrFreshyFreeze">
            </shreddit-post>
            <shreddit-player post-promoted src="https://v.redd.it/ad/HLSPlaylist.m3u8"></shreddit-player>'''

        result = self.ie._extract_webpage('https://www.reddit.com/comments/6t75wq/', '6t75wq')

        self.assertEqual(result['_type'], 'url_transparent')
        self.assertEqual(result['url'], 'https://youtu.be/4arBraMyp0Q')
        self.assertEqual(result['display_id'], '6t75wq')
        self.assertEqual(result['uploader'], 'MrFreshyFreeze')

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
