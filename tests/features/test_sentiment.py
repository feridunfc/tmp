from algo5.features.sentiment import simple_sentiment
def test_simple_sentiment():
    assert simple_sentiment("This is good and green") > 0
    assert simple_sentiment("bad red loss") < 0
    assert simple_sentiment("") == 0.0
