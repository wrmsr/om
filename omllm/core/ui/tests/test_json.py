from ..json import render_obj_json_text


def test_render():
    t = render_obj_json_text({
        'hi': ['there', '!'],
    })

    print(t)
