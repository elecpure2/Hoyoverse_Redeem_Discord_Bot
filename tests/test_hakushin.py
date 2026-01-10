try:
    import hakushin
    print(f"hakushin module found: {hakushin}")
    if hasattr(hakushin, 'Game'):
        print("hakushin.Game found (hakushin-py style)")
    else:
        print("hakushin.Game NOT found")

    try:
        from hakushin.enums import Game
        print("hakushin.enums.Game found (original usage style)")
    except ImportError:
        print("hakushin.enums.Game NOT found")
        
except ImportError as e:
    print(f"ImportError: {e}")
