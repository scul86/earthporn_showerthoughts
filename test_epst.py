import ep_st


def test_fix_imgur():
    assert ep_st.fix_imgur('https://imgur.com/12345') == 'https://i.imgur.com/12345.png'
    assert ep_st.fix_imgur('http://imgur.com/12345') == 'http://i.imgur.com/12345.png'
    assert ep_st.fix_imgur('i.imgur.com') == 'i.imgur.com'
    assert ep_st.fix_imgur('imgtest.com') == 'imgtest.com'
