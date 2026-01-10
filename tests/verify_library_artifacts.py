import asyncio
import hakushin
from hakushin import Game, Language

async def main():
    print("Checking GI Artifacts via Library...")
    try:
        async with hakushin.HakushinAPI(Game.GI, Language.KO) as client:
            sets = await client.fetch_artifact_sets()
            print(f"GI Sets: {len(sets)}")
            if sets:
                print(f"Sample: {sets[0].name} (ID: {sets[0].id})")
    except Exception as e:
        print(f"GI Error: {e}")

    print("\nChecking HSR Relics via Library...")
    try:
        async with hakushin.HakushinAPI(Game.HSR, Language.KO) as client:
            sets = await client.fetch_relic_sets()
            print(f"HSR Sets: {len(sets)}")
            if sets:
                print(f"Sample: {sets[0].name} (ID: {sets[0].id})")
    except Exception as e:
        print(f"HSR Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
