import asyncio
import sys
from shopbot import main

if __name__ == "__main__":
    # Set proper event loop policy for Windows
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Bot stopped with error: {e}")