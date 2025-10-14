from mangagraph import Mangagraph, MangagraphError
import asyncio

# === tests ===
# python -m tests.__init__
async def test():
    try:
        parser = Mangagraph()
        results = await parser.process_chapters(
            'https://mangalib.me/ru/manga/7965--chainsaw-man',
            chapter_nums=[90, 91, 92]
        )

        print("Parsed chapters:\n")
        for num, (toc, mirror) in results.items():
            print(f"📖 Chapter {num}")
            print(f"   TOC: {toc}")
            print(f"   Mirror: {mirror}\n")

    except MangagraphError as e:
        print(f"Parser error: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(test())
    except (KeyboardInterrupt, SystemExit):
        print('Sayonara!')