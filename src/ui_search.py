#!/usr/bin/env python3
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

from .search_backend import search_conversations_fallback, search_messages


class SearchWorker(QRunnable):
    def __init__(
        self,
        db_path: str,
        query: str,
        bot: Optional[str],
        start: Optional[str],
        end: Optional[str],
        limit: int = 200
    ):
        super().__init__()
        self.db_path = db_path
        self.query = query
        self.bot = bot
        self.start = start
        self.end = end
        self.limit = limit
        self._callback = None

    def set_callback(self, cb):
        self._callback = cb
        return self

    def run(self):
        try:
            results = search_messages(
                self.db_path, self.query, self.bot, self.start, self.end,
                self.limit, 0
            )
            # Fallback if no results from messages table
            if not results:
                results = search_conversations_fallback(
                    self.db_path, self.query, self.bot, self.start, self.end,
                    self.limit, 0
                )
        except Exception as e:
            print(f"Search error: {e}")
            results = []

        if self._callback:
            self._callback(results)


class SearchController(QObject):
    resultsReady = pyqtSignal(list)

    def __init__(self, db_path: str, thread_pool: Optional[QThreadPool] = None):
        super().__init__()
        self.db_path = str(Path(db_path))
        self.pool = thread_pool or QThreadPool.globalInstance()

    def execute(
        self,
        query: str,
        bot: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 200
    ):
        worker = SearchWorker(
            self.db_path, query, bot, start, end, limit
        ).set_callback(lambda rows: self.resultsReady.emit(rows))
        self.pool.start(worker)
        ).set_callback(lambda rows: self.resultsReady.emit(rows))
        self.pool.start(worker)
