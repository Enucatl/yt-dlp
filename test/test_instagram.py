from test.helper import FakeYDL
from yt_dlp.extractor.instagram import InstagramIE


def test_image_product() -> None:
    info = InstagramIE(FakeYDL())._extract_product({
        'pk': '123',
        'user': {'username': 'tester'},
        'image_versions2': {'candidates': [{
            'url': 'https://cdn.example/image.jpg',
            'width': 1080,
            'height': 1080,
        }]},
    }, get_comments=False)

    assert info['url'] == 'https://cdn.example/image.jpg'
    assert info['ext'] == 'jpg'
    assert info['vcodec'] == 'none'
    assert (info['width'], info['height']) == (1080, 1080)
    assert 'formats' not in info


def test_mixed_carousel() -> None:
    info = InstagramIE(FakeYDL())._extract_product({
        'pk': '123',
        'user': {'username': 'tester'},
        'carousel_media': [{
            'pk': '124',
            'image_versions2': {'candidates': [{
                'url': 'https://cdn.example/image.webp',
                'width': 640,
                'height': 480,
            }]},
        }, {
            'pk': '125',
            'video_versions': [{
                'url': 'https://cdn.example/video.mp4',
                'width': 1280,
                'height': 720,
            }],
        }],
    }, get_comments=False)

    assert info['_type'] == 'playlist'
    assert info['entries'][0]['url'] == 'https://cdn.example/image.webp'
    assert info['entries'][0]['vcodec'] == 'none'
    assert 'formats' not in info['entries'][0]
    assert info['entries'][1]['formats'][0]['url'] == 'https://cdn.example/video.mp4'
