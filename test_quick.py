import asyncio
from backend.agents.test_server_client import TestServerClientContext

async def test():
    async with TestServerClientContext() as client:
        # Hole Verfahren
        verfahren = await client.search_verfahren(limit=1)
        if verfahren:
            v = verfahren[0]
            print(f"Verfahren: {v['verfahren_id']}")
            print(f"Anlage: {v['bst_nr']}/{v['anl_nr']}")
            
            # Hole komplette Daten
            anlage = await client.get_anlage_complete(v['bst_nr'], v['anl_nr'])
            if anlage:
                print(f"✅ Anlage gefunden!")
                print(f"Name: {anlage.anlage.bst_name}")
                print(f"Verfahren: {len(anlage.verfahren)}")
                print(f"Messungen: {len(anlage.messungen)}")
                print(f"Statistik: {anlage.statistik}")
            else:
                print("⚠️ Anlage nicht gefunden")

asyncio.run(test())
