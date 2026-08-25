# store.py
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QScrollArea,
    QMessageBox,
    QProgressBar,
)


# ============================================================
# CONFIG
# ============================================================

STORE_NAME = "OliStore"

# Поменяй на адрес своего сервера.
CATALOG_URL = "https://YOUR-SERVER.example/olisto­re/apps.json"

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "store_cache"
DOWNLOAD_DIR = BASE_DIR / "downloads"
INSTALLED_DIR = BASE_DIR / "installed"
ICON_DIR = CACHE_DIR / "icons"

for directory in (
    CACHE_DIR,
    DOWNLOAD_DIR,
    INSTALLED_DIR,
    ICON_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# PLATFORM
# ============================================================

def detect_platform() -> str:
    """
    Для разработки на Mac/PC возвращаем desktop.
    На реальном TV сюда можно подключить определение
    конкретной платформы.
    """

    if sys.platform.startswith("win"):
        return "desktop-windows"

    if sys.platform == "darwin":
        return "desktop-macos"

    if sys.platform.startswith("linux"):
        return "desktop-linux"

    return "unknown"


PLATFORM = detect_platform()


# ============================================================
# APP MODEL
# ============================================================

@dataclass
class StoreApp:
    app_id: str
    name: str
    category: str
    description: str
    version: str

    icon_url: str = ""
    package_url: str = ""

    size: int = 0
    sha256: str = ""

    installed: bool = False
    free: bool = True

    platforms: tuple[str, ...] = ()


# ============================================================
# HTTP
# ============================================================

class HTTPClient:

    USER_AGENT = "OliStore/1.0"

    @classmethod
    def get_bytes(cls, url: str, timeout: int = 15) -> bytes:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": cls.USER_AGENT,
                "Accept": "*/*",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            return response.read()

    @classmethod
    def get_json(cls, url: str) -> dict:

        data = cls.get_bytes(url)

        return json.loads(
            data.decode("utf-8")
        )

    @classmethod
    def download(
        cls,
        url: str,
        destination: Path,
        progress_callback=None,
    ):

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": cls.USER_AGENT,
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:

            total = response.headers.get(
                "Content-Length"
            )

            total = int(total) if total else 0

            downloaded = 0

            with open(destination, "wb") as output:

                while True:

                    chunk = response.read(128 * 1024)

                    if not chunk:
                        break

                    output.write(chunk)

                    downloaded += len(chunk)

                    if progress_callback:

                        progress_callback(
                            downloaded,
                            total,
                        )


# ============================================================
# CATALOG
# ============================================================

class CatalogManager:

    def __init__(self, url: str):

        self.url = url

        self.apps: list[StoreApp] = []

    def load(self):

        print(
            f"[OliStore] Loading catalog: {self.url}"
        )

        data = HTTPClient.get_json(
            self.url
        )

        applications = data.get(
            "apps",
            [],
        )

        result = []

        for item in applications:

            platforms = tuple(
                item.get(
                    "platforms",
                    [],
                )
            )

            # Если сервер указал платформы,
            # показываем только совместимые.
            if platforms:

                if PLATFORM not in platforms:
                    continue

            app = StoreApp(
                app_id=item["id"],
                name=item.get(
                    "name",
                    item["id"],
                ),
                category=item.get(
                    "category",
                    "Другое",
                ),
                description=item.get(
                    "description",
                    "",
                ),
                version=str(
                    item.get(
                        "version",
                        "1.0",
                    )
                ),
                icon_url=item.get(
                    "icon",
                    "",
                ),
                package_url=item.get(
                    "package",
                    "",
                ),
                size=int(
                    item.get(
                        "size",
                        0,
                    )
                ),
                sha256=item.get(
                    "sha256",
                    "",
                ),
                free=bool(
                    item.get(
                        "free",
                        True,
                    )
                ),
                platforms=platforms,
            )

            app.installed = self.is_installed(
                app
            )

            result.append(app)

        self.apps = result

        print(
            f"[OliStore] Apps available: {len(result)}"
        )

        return result

    def is_installed(
        self,
        app: StoreApp,
    ) -> bool:

        marker = (
            INSTALLED_DIR
            / app.app_id
            / "installed.json"
        )

        return marker.exists()

    def mark_installed(
        self,
        app: StoreApp,
    ):

        directory = (
            INSTALLED_DIR
            / app.app_id
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        marker = (
            directory
            / "installed.json"
        )

        marker.write_text(
            json.dumps(
                {
                    "id": app.app_id,
                    "version": app.version,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


# ============================================================
# DOWNLOAD WORKER
# ============================================================

class DownloadWorker(QThread):

    progress = pyqtSignal(int)

    finished_ok = pyqtSignal(object)

    failed = pyqtSignal(str)

    def __init__(
        self,
        app: StoreApp,
    ):

        super().__init__()

        self.app = app

    def run(self):

        try:

            if not self.app.package_url:

                raise RuntimeError(
                    "У приложения отсутствует package URL."
                )

            filename = (
                f"{self.app.app_id}-"
                f"{self.app.version}.pkg"
            )

            destination = (
                DOWNLOAD_DIR
                / filename
            )

            def update(
                downloaded,
                total,
            ):

                if total > 0:

                    percent = int(
                        downloaded
                        * 100
                        / total
                    )

                    self.progress.emit(
                        max(
                            0,
                            min(
                                100,
                                percent,
                            ),
                        )
                    )

            print(
                "[OliStore] Downloading:",
                self.app.package_url,
            )

            HTTPClient.download(
                self.app.package_url,
                destination,
                update,
            )

            # ------------------------------------------------
            # SHA-256
            # ------------------------------------------------

            if self.app.sha256:

                print(
                    "[OliStore] Checking SHA-256..."
                )

                actual = sha256_file(
                    destination
                )

                expected = (
                    self.app.sha256
                    .lower()
                    .strip()
                )

                if actual.lower() != expected:

                    destination.unlink(
                        missing_ok=True
                    )

                    raise RuntimeError(
                        "Проверка SHA-256 не пройдена."
                    )

            self.progress.emit(100)

            self.finished_ok.emit(
                destination
            )

        except Exception as error:

            self.failed.emit(
                str(error)
            )


# ============================================================
# HASH
# ============================================================

def sha256_file(
    filename: Path,
) -> str:

    digest = hashlib.sha256()

    with open(
        filename,
        "rb",
    ) as file:

        while True:

            block = file.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


# ============================================================
# PACKAGE INSTALLER
# ============================================================

class PackageInstaller:

    @staticmethod
    def install(
        app: StoreApp,
        package: Path,
    ):

        target = (
            INSTALLED_DIR
            / app.app_id
        )

        temp = Path(
            tempfile.mkdtemp(
                prefix="olisto­re-"
            )
        )

        try:

            # Пока используем ZIP как формат разработки.
            # На реальном TV здесь будет platform-specific
            # installer backend.
            if package.suffix.lower() == ".zip":

                shutil.unpack_archive(
                    package,
                    temp,
                )

            else:

                # Для собственного package manager
                # оставляем файл пакета.
                temp_package = (
                    temp / package.name
                )

                shutil.copy2(
                    package,
                    temp_package,
                )

            if target.exists():

                backup = target.with_name(
                    target.name + ".backup"
                )

                if backup.exists():

                    shutil.rmtree(
                        backup,
                        ignore_errors=True,
                    )

                shutil.move(
                    str(target),
                    str(backup),
                )

            target.mkdir(
                parents=True,
                exist_ok=True,
            )

            for item in temp.iterdir():

                destination = (
                    target / item.name
                )

                if item.is_dir():

                    shutil.copytree(
                        item,
                        destination,
                    )

                else:

                    shutil.copy2(
                        item,
                        destination,
                    )

            print(
                "[OliStore] Installed:",
                app.name,
            )

            return True

        finally:

            shutil.rmtree(
                temp,
                ignore_errors=True,
            )


# ============================================================
# APP CARD
# ============================================================

class AppCard(QPushButton):

    def __init__(
        self,
        app: StoreApp,
    ):

        super().__init__()

        self.app = app

        self.setFixedSize(
            310,
            112,
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        self.setStyleSheet("""
            QPushButton {
                background: #eeeeee;
                border: 1px solid #c5c5c5;
                border-radius: 3px;
                text-align: left;
            }

            QPushButton:hover {
                border: 2px solid #63b9eb;
            }

            QPushButton:focus {
                background: #ffffff;
                border: 3px solid #39a9e8;
            }

            QPushButton:pressed {
                background: #d4d4d4;
            }
        """)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            9,
            8,
            9,
            8,
        )

        icon = QLabel()

        icon.setFixedSize(
            82,
            78,
        )

        icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.icon_label = icon

        self.load_icon()

        text = QVBoxLayout()

        name = QLabel(
            app.name
        )

        name.setStyleSheet("""
            color: #222222;
            font-size: 18px;
            font-weight: bold;
        """)

        category = QLabel(
            app.category
        )

        category.setStyleSheet("""
            color: #777777;
            font-size: 14px;
        """)

        status = QLabel(
            "установл."
            if app.installed
            else "Бесплатно"
            if app.free
            else "Подробнее"
        )

        status.setStyleSheet("""
            color: #333333;
            font-size: 14px;
        """)

        text.addWidget(name)
        text.addWidget(category)
        text.addStretch()
        text.addWidget(status)

        layout.addWidget(icon)
        layout.addLayout(text)

    def load_icon(self):

        if not self.app.icon_url:

            self.placeholder_icon()
            return

        try:

            filename = (
                ICON_DIR
                / f"{self.app.app_id}.png"
            )

            if not filename.exists():

                data = HTTPClient.get_bytes(
                    self.app.icon_url
                )

                filename.write_bytes(
                    data
                )

            pixmap = QPixmap(
                str(filename)
            )

            if not pixmap.isNull():

                pixmap = pixmap.scaled(
                    QSize(76, 70),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                self.icon_label.setPixmap(
                    pixmap
                )

                return

        except Exception as error:

            print(
                "[OliStore] Icon error:",
                error,
            )

        self.placeholder_icon()

    def placeholder_icon(self):

        self.icon_label.setStyleSheet("""
            background: #5b5b5b;
            border-radius: 5px;
            color: white;
            font-size: 28px;
            font-weight: bold;
        """)

        self.icon_label.setText(
            self.app.name[:1].upper()
        )


# ============================================================
# STORE
# ============================================================

class OliStore(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            STORE_NAME
        )

        self.resize(
            1366,
            768,
        )

        self.catalog = CatalogManager(
            CATALOG_URL
        )

        self.apps: list[StoreApp] = []

        self.current_category = "Все"

        self.build_ui()

        self.load_catalog()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):

        self.setStyleSheet("""
            QWidget {
                font-family:
                    Arial,
                    Helvetica,
                    sans-serif;
            }

            QLineEdit {
                background: #eeeeee;
                color: #222222;
                border: 2px solid #777777;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 18px;
            }
        """)

        root = QVBoxLayout(self)

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root.setSpacing(0)

        # ====================================================
        # TOP
        # ====================================================

        top = QFrame()

        top.setFixedHeight(
            62
        )

        top.setStyleSheet("""
            QFrame {
                background:
                    qlineargradient(
                        x1: 0,
                        y1: 0,
                        x2: 0,
                        y2: 1,
                        stop: 0 #050505,
                        stop: .5 #181818,
                        stop: 1 #050505
                    );
            }
        """)

        top_layout = QHBoxLayout(
            top
        )

        title = QLabel(
            "OliStore"
        )

        title.setStyleSheet("""
            color: white;
            font-size: 25px;
            font-weight: bold;
        """)

        top_layout.addWidget(
            title
        )

        top_layout.addStretch()

        self.connection_label = QLabel(
            "Подключение..."
        )

        self.connection_label.setStyleSheet("""
            color: #aaaaaa;
            font-size: 14px;
        """)

        top_layout.addWidget(
            self.connection_label
        )

        root.addWidget(
            top
        )

        # ====================================================
        # FEATURED
        # ====================================================

        featured = QFrame()

        featured.setFixedHeight(
            150
        )

        featured.setStyleSheet("""
            background: #080808;
        """)

        featured_layout = QHBoxLayout(
            featured
        )

        featured_layout.setContentsMargins(
            15,
            10,
            15,
            10,
        )

        featured_layout.setSpacing(
            12
        )

        for title in (
            "Новые возможности",
            "Видео",
            "Игры",
            "Информация",
            "Рекомендуем",
        ):

            card = QLabel(
                title
            )

            card.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            card.setFixedSize(
                220,
                120,
            )

            card.setStyleSheet("""
                background:
                    qlineargradient(
                        x1: 0,
                        y1: 0,
                        x2: 1,
                        y2: 1,
                        stop: 0 #202020,
                        stop: .5 #555555,
                        stop: 1 #111111
                    );

                color: white;

                font-size: 17px;
                font-weight: bold;

                border: 1px solid #444444;
            """)

            featured_layout.addWidget(
                card
            )

        root.addWidget(
            featured
        )

        # ====================================================
        # MAIN CONTENT
        # ====================================================

        content = QHBoxLayout()

        content.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        content.setSpacing(
            12
        )

        # ----------------------------------------------------
        # LEFT MENU
        # ----------------------------------------------------

        left = QFrame()

        left.setFixedWidth(
            325
        )

        left.setStyleSheet("""
            QFrame {
                background:
                    qlineargradient(
                        x1: 0,
                        y1: 0,
                        x2: 0,
                        y2: 1,
                        stop: 0 #eeeeee,
                        stop: 1 #c8c8c8
                    );

                border-radius: 9px;
            }
        """)

        left_layout = QVBoxLayout(
            left
        )

        left_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Поиск приложений"
        )

        self.search.textChanged.connect(
            self.refresh_grid
        )

        left_layout.addWidget(
            self.search
        )

        categories = [
            "Наиболее популярные",
            "Видео",
            "Игра",
            "Спорт",
            "Стиль",
            "Информация",
            "Образование",
            "Загруз. прилож.",
            "Справка",
        ]

        for category in categories:

            button = QPushButton(
                category
            )

            button.setFixedHeight(
                38
            )

            button.setFocusPolicy(
                Qt.FocusPolicy.StrongFocus
            )

            button.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #202020;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 18px;
                    border-radius: 4px;
                }

                QPushButton:hover,
                QPushButton:focus {
                    background: #596b83;
                    color: white;
                    border: 2px solid #8bd6ff;
                }
            """)

            button.clicked.connect(
                lambda checked=False,
                value=category:
                self.select_category(value)
            )

            left_layout.addWidget(
                button
            )

        left_layout.addStretch()

        content.addWidget(
            left
        )

        # ----------------------------------------------------
        # RIGHT
        # ----------------------------------------------------

        right = QVBoxLayout()

        header = QFrame()

        header.setFixedHeight(
            62
        )

        header.setStyleSheet("""
            QFrame {
                background:
                    qlineargradient(
                        x1: 0,
                        y1: 0,
                        x2: 0,
                        y2: 1,
                        stop: 0 #eeeeee,
                        stop: 1 #bcbcbc
                    );

                border-radius: 8px;
            }
        """)

        header_layout = QHBoxLayout(
            header
        )

        self.category_label = QLabel(
            "☷   Все"
        )

        self.category_label.setStyleSheet("""
            color: #333333;
            font-size: 22px;
            font-weight: bold;
        """)

        header_layout.addWidget(
            self.category_label
        )

        header_layout.addStretch()

        self.count_label = QLabel(
            "0"
        )

        self.count_label.setStyleSheet("""
            color: #333333;
            font-size: 17px;
        """)

        header_layout.addWidget(
            self.count_label
        )

        right.addWidget(
            header
        )

        # ----------------------------------------------------
        # GRID
        # ----------------------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #d4d4d4;
            }
        """)

        self.grid_widget = QWidget()

        self.grid_widget.setStyleSheet(
            "background: #d4d4d4;"
        )

        self.grid = QGridLayout(
            self.grid_widget
        )

        self.grid.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        self.grid.setHorizontalSpacing(
            15
        )

        self.grid.setVerticalSpacing(
            12
        )

        scroll.setWidget(
            self.grid_widget
        )

        right.addWidget(
            scroll,
            1,
        )

        content.addLayout(
            right,
            1,
        )

        root.addLayout(
            content,
            1,
        )

        # ====================================================
        # BOTTOM
        # ====================================================

        bottom = QFrame()

        bottom.setFixedHeight(
            42
        )

        bottom.setStyleSheet(
            "background: #050505;"
        )

        bottom_layout = QHBoxLayout(
            bottom
        )

        bottom_layout.addStretch()

        help_label = QLabel(
            "OK Выбрать    "
            "Инструм.    "
            "↩ Возврат"
        )

        help_label.setStyleSheet("""
            color: #dddddd;
            font-size: 15px;
        """)

        bottom_layout.addWidget(
            help_label
        )

        root.addWidget(
            bottom
        )

    # --------------------------------------------------------
    # CATALOG
    # --------------------------------------------------------

    def load_catalog(self):

        try:

            self.apps = (
                self.catalog.load()
            )

            self.connection_label.setText(
                "Онлайн"
            )

            self.connection_label.setStyleSheet("""
                color: #8fd16b;
                font-size: 14px;
            """)

            self.refresh_grid()

        except Exception as error:

            self.connection_label.setText(
                "Офлайн"
            )

            self.connection_label.setStyleSheet("""
                color: #e08a8a;
                font-size: 14px;
            """)

            QMessageBox.warning(
                self,
                "OliStore",
                "Не удалось загрузить каталог:\n\n"
                + str(error),
            )

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    def select_category(
        self,
        category: str,
    ):

        if category in (
            "Наиболее популярные",
            "Загруз. прилож.",
        ):

            self.current_category = "Все"

        elif category in (
            "Справка",
        ):

            self.current_category = "Справка"

        else:

            self.current_category = category

        self.category_label.setText(
            f"☷   {category}"
        )

        self.refresh_grid()

    # --------------------------------------------------------
    # GRID
    # --------------------------------------------------------

    def refresh_grid(self):

        while self.grid.count():

            item = self.grid.takeAt(
                0
            )

            widget = item.widget()

            if widget:

                widget.deleteLater()

        apps = list(
            self.apps
        )

        if (
            self.current_category
            not in ("Все", "Справка")
        ):

            apps = [
                app
                for app in apps
                if app.category
                == self.current_category
            ]

        query = (
            self.search.text()
            .strip()
            .lower()
        )

        if query:

            apps = [
                app
                for app in apps
                if (
                    query in app.name.lower()
                    or query in app.description.lower()
                )
            ]

        self.count_label.setText(
            str(len(apps))
        )

        for index, app in enumerate(
            apps
        ):

            row = index // 3
            column = index % 3

            card = AppCard(
                app
            )

            card.clicked.connect(
                lambda checked=False,
                selected=app:
                self.open_app(selected)
            )

            self.grid.addWidget(
                card,
                row,
                column,
            )

        if self.grid.count():

            first = (
                self.grid
                .itemAt(0)
                .widget()
            )

            if first:

                first.setFocus()

    # --------------------------------------------------------
    # APP PAGE
    # --------------------------------------------------------

    def open_app(
        self,
        app: StoreApp,
    ):

        dialog = QFrame(
            self
        )

        dialog.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )

        dialog.setGeometry(
            self.width() // 2 - 320,
            self.height() // 2 - 190,
            640,
            380,
        )

        dialog.setStyleSheet("""
            QFrame {
                background: #e7e7e7;
                border: 3px solid #4aafe8;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(
            dialog
        )

        title = QLabel(
            app.name
        )

        title.setStyleSheet("""
            color: #222222;
            font-size: 27px;
            font-weight: bold;
        """)

        version = QLabel(
            f"Версия {app.version}"
        )

        version.setStyleSheet("""
            color: #666666;
            font-size: 15px;
        """)

        description = QLabel(
            app.description
        )

        description.setWordWrap(
            True
        )

        description.setStyleSheet("""
            color: #333333;
            font-size: 17px;
        """)

        layout.addWidget(
            title
        )

        layout.addWidget(
            version
        )

        layout.addSpacing(
            20
        )

        layout.addWidget(
            description
        )

        layout.addStretch()

        progress = QProgressBar()

        progress.setValue(
            0
        )

        progress.hide()

        layout.addWidget(
            progress
        )

        buttons = QHBoxLayout()

        action = QPushButton(
            "Открыть"
            if app.installed
            else "Установить"
        )

        close = QPushButton(
            "Возврат"
        )

        for button in (
            action,
            close,
        ):

            button.setFixedHeight(
                48
            )

            button.setStyleSheet("""
                QPushButton {
                    background: #d5d5d5;
                    color: #222222;
                    border: 2px solid #999999;
                    border-radius: 5px;
                    font-size: 17px;
                    padding: 5px 20px;
                }

                QPushButton:focus {
                    background: #f4f4f4;
                    border: 3px solid #45afe8;
                }
            """)

        close.clicked.connect(
            dialog.deleteLater
        )

        if app.installed:

            action.clicked.connect(
                lambda:
                self.launch_app(app)
            )

        else:

            action.clicked.connect(
                lambda:
                self.start_install(
                    app,
                    action,
                    progress,
                    dialog,
                )
            )

        buttons.addWidget(
            action
        )

        buttons.addWidget(
            close
        )

        layout.addLayout(
            buttons
        )

        dialog.show()

        action.setFocus()

    # --------------------------------------------------------
    # DOWNLOAD + INSTALL
    # --------------------------------------------------------

    def start_install(
        self,
        app: StoreApp,
        button: QPushButton,
        progress: QProgressBar,
        dialog: QFrame,
    ):

        if not app.package_url:

            QMessageBox.warning(
                dialog,
                "OliStore",
                "Для этого приложения "
                "не указан пакет.",
            )

            return

        button.setEnabled(
            False
        )

        progress.show()

        self.worker = DownloadWorker(
            app
        )

        self.worker.progress.connect(
            progress.setValue
        )

        self.worker.failed.connect(
            lambda error:
            self.install_failed(
                error,
                button,
                progress,
            )
        )

        self.worker.finished_ok.connect(
            lambda package:
            self.install_downloaded(
                app,
                package,
                button,
                progress,
            )
        )

        self.worker.start()

    def install_downloaded(
        self,
        app: StoreApp,
        package: Path,
        button: QPushButton,
        progress: QProgressBar,
    ):

        try:

            PackageInstaller.install(
                app,
                package,
            )

            self.catalog.mark_installed(
                app
            )

            app.installed = True

            button.setText(
                "Открыть"
            )

            button.setEnabled(
                True
            )

            progress.setValue(
                100
            )

            self.refresh_grid()

            print(
                "[OliStore] Installation OK:",
                app.name,
            )

        except Exception as error:

            button.setEnabled(
                True
            )

            QMessageBox.critical(
                self,
                "Ошибка установки",
                str(error),
            )

    def install_failed(
        self,
        error: str,
        button: QPushButton,
        progress: QProgressBar,
    ):

        button.setEnabled(
            True
        )

        progress.hide()

        QMessageBox.warning(
            self,
            "OliStore",
            "Ошибка загрузки:\n\n"
            + error,
        )

    # --------------------------------------------------------
    # LAUNCH
    # --------------------------------------------------------

    def launch_app(
        self,
        app: StoreApp,
    ):

        directory = (
            INSTALLED_DIR
            / app.app_id
        )

        # Стандартный entry point
        candidates = [
            directory / "main.py",
            directory / "app.py",
            directory / "run.py",
        ]

        executable = next(
            (
                path
                for path in candidates
                if path.exists()
            ),
            None,
        )

        if executable:

            try:

                subprocess.Popen(
                    [
                        sys.executable,
                        str(executable),
                    ],
                    cwd=str(directory),
                )

                return

            except Exception as error:

                QMessageBox.warning(
                    self,
                    "OliStore",
                    f"Не удалось запустить "
                    f"{app.name}:\n\n{error}",
                )

                return

        QMessageBox.information(
            self,
            "OliStore",
            f"{app.name}\n\n"
            "Приложение установлено.",
        )


# ============================================================
# MAIN
# ============================================================

def main():

    application = QApplication(
        sys.argv
    )

    application.setApplicationName(
        STORE_NAME
    )

    store = OliStore()

    # Для разработки можно убрать fullscreen.
    # На телевизоре оставить.
    if PLATFORM.startswith(
        "desktop"
    ):

        store.show()

    else:

        store.showFullScreen()

    sys.exit(
        application.exec()
    )


if __name__ == "__main__":
    main()
