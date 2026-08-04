if __name__ == '__main__':
    from .framers import _main as _framers_main
    from .searches import _main as _searches_main
    from .writes import _main as _writes_main

    _framers_main()
    _searches_main()
    _writes_main()
