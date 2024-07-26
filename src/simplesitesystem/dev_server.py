import asyncio
import os

import aiohttp
from aiohttp import web
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from simplesitesystem.build import build_internal
from simplesitesystem.tools import strip_exts


def that_output(e: str, l: str):
    return strip_exts(os.path.join(l, os.path.relpath(e, "src"))) + ".html"


def create_websocket_handler(
    source_dir: str,
    output_dir: str,
    strings_file: str,
    data_file: str,
    no_symlink_assets: bool = False,
):
    class ReloadingHandler(FileSystemEventHandler):
        def __init__(
            self,
            websocket,
            *args,
            **kwargs,
        ):
            self.websocket = websocket
            self.pathname: str | None = None
            self.used = False
            super().__init__(*args, **kwargs)

        def on_modified(self, event: FileSystemEvent):
            if event.is_directory:
                return
            build_internal(
                source_dir,
                output_dir,
                strings_file,
                data_file,
                no_symlink_assets,
                True,
            )
            if not self.used:
                asyncio.run(self.websocket.send_str("reload"))
                self.used = True

        def on_moved(self, event: FileSystemEvent) -> None:
            build_internal(
                source_dir,
                output_dir,
                strings_file,
                data_file,
                no_symlink_assets,
                True,
            )
            if self.used:
                return
            output_paths = {
                that_output(event.src_path, locale): that_output(
                    event.dest_path, locale
                )
                for locale in ["/", "/en", "/jp"]
            }
            print(output_paths)
            for src_output, dest_output in output_paths.items():
                if self.pathname == src_output:
                    asyncio.run(self.websocket.send_str(f"go_to {dest_output}"))
            self.used = True

    async def websocket_handler(request):
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        print("WebSocket connection opened")

        handler = ReloadingHandler(websocket)
        observer = Observer()
        observer.schedule(handler, source_dir, recursive=True)
        observer.start()

        async for msg in websocket:
            if msg.type == aiohttp.WSMsgType.TEXT:
                # noinspection PyUnresolvedReferences
                handler.pathname = msg.data
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(
                    "WebSocket connection closed with exception %s"
                    % websocket.exception()
                )

        observer.stop()

        print("WebSocket connection closed")
        return websocket

    return websocket_handler
