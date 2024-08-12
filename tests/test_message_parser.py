from wikibot.parser import MessageParser, Messages, MessageTypes


async def test_matches_what_is():
    p = MessageParser("Що таке Головна сторінка?")
    message_type, matches = await p.get_matches()
    assert message_type == Messages.WHATIS
    assert len(matches) == 1 and matches[0] == "Головна сторінка"


async def test_matches_who_is():
    p = MessageParser("хто такий зеленський")
    message_type, matches = await p.get_matches()
    assert message_type == Messages.WHATIS
    assert len(matches) == 1 and matches[0] == "зеленський"


async def test_contains_ukwikibot():
    p = MessageParser("Чуєш, @ukwikibot, як ти?")
    message_type, _ = await p.get_matches()
    assert message_type == Messages.UKWIKIBOT


async def test_get_response_link():
    p = MessageParser("Some text [[рейган]] some text")
    response, message_type = await p.get_response()
    assert message_type == MessageTypes.TEXT
    assert response[0] == "https://uk.wikipedia.org/wiki/Рейган"
    p = MessageParser("Some text [[oooòoooo]] some text")
    assert len((await p.get_response())[0]) == 0


async def test_get_image():
    p = MessageParser("Знайди фото Рейгана")
    response, message_type = await p.get_response()
    assert message_type == MessageTypes.IMAGE
    assert len(response) == 1
    assert isinstance(response[0][0], bytes)
    assert "File:" in response[0][1]
    assert "Category:Ronald Reagan" in response[0][1]


async def test_get_coords():
    p = MessageParser("Де розташований Київ")
    response, message_type = await p.get_response()
    assert message_type == MessageTypes.COORDS
    assert len(response) == 1
    lat, lon = response[0]
    assert round(lat, 2) == 50.45
    assert round(lon, 2) == 30.52
