from wikibot.wiki import WikiManager


async def test_genitive_transform():
    manager = WikiManager()
    text = await manager.genitive_transform("Володимира Зеленського")
    text2 = await manager.genitive_transform("Володимир Зеленського")
    text3 = await manager.genitive_transform("Володимир зеленського")
    assert text == "Володимир Зеленський"
    assert text == text2
    assert text3 == "Володимир зеленський"


async def test_genitive_search():
    manager = WikiManager()
    kyiv = await manager.genitive_search("Києва")
    assert str(kyiv) == "[[uk:Київ]]"


async def test_genitive_search_image():
    manager = WikiManager()
    kyiv, description_url, category = await manager.get_images_genitive("Києва")
    assert kyiv.startswith("https://upload.wikimedia.org/wikipedia/commons/thumb/")
    assert description_url.startswith("https://commons.wikimedia.org/")
    assert category == "Kyiv"


async def test_search():
    manager = WikiManager()
    lviv = await manager.search("Львів")
    assert "місто на заході України" in lviv


async def test_coordinates():
    manager = WikiManager()
    lviv = await manager.genitive_search("Львова")
    lat, long = await manager.get_coords(lviv)
    assert round(lat, 2), round(long, 2) == (49.84, 24.03)


async def test_day_of_death():
    manager = WikiManager()
    page = await manager.genitive_search("Джордж Буш старший")
    assert await manager.get_deathday(page) == "30 листопада 2018"


async def test_birthday():
    manager = WikiManager()
    page = await manager.genitive_search("Рейган")
    assert await manager.get_birthday(page) == "6 лютого 1911"
