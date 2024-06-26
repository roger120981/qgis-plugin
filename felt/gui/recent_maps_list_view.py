"""
Widgets for selection from Recent Maps
"""

import platform
from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    QModelIndex,
    QSize,
    QRectF,
    QPointF,
    QItemSelectionModel
)
from qgis.PyQt.QtGui import (
    QFontMetrics,
    QPainter,
    QBrush,
    QPen,
    QColor,
    QFont,
    QImage,
    QPalette
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QAbstractItemView,
    QListView,
    QApplication,
    QStyle,
    QVBoxLayout,
)
from qgis.gui import QgsFilterLineEdit

from ..core import Map, RecentMapsModel


class RecentMapDelegate(QStyledItemDelegate):
    """
    Custom delegate for rendering map details in a list
    """

    THUMBNAIL_CORNER_RADIUS = 4
    VERTICAL_MARGIN = 4
    HORIZONTAL_MARGIN = 5
    THUMBNAIL_RATIO = 4 / 3
    THUMBNAIL_MARGIN = 0
    BORDER_WIDTH_PIXELS = 1

    SELECTED_ROW_COLOR = QColor("#fed9e3")
    HEADING_COLOR = QColor(0, 0, 0)
    SUBHEADING_COLOR = QColor(153, 153, 153)

    def process_thumbnail(self,
                          thumbnail: QImage,
                          height: int,
                          is_new_map_thumbnail: bool,
                          device_pixel_ratio: float) -> QImage:
        """
        Processes a raw thumbnail image, resizing to required size and
        rounding off corners
        """
        target_size = QSize(
            int(height * RecentMapDelegate.THUMBNAIL_RATIO), height
        )
        image_ratio = thumbnail.width() / thumbnail.height()
        uncropped_thumbnail_width = int(image_ratio *
                                        height *
                                        device_pixel_ratio)
        scaled = thumbnail.scaled(
            QSize(uncropped_thumbnail_width, int(height * device_pixel_ratio)),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        im_out = QImage(int(target_size.width() * device_pixel_ratio),
                        int(target_size.height() * device_pixel_ratio),
                        QImage.Format_ARGB32)
        im_out.fill(Qt.transparent)
        painter = QPainter(im_out)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawRoundedRect(
            QRectF(1 * device_pixel_ratio,
                   1 * device_pixel_ratio,
                   (target_size.width() - 2) * device_pixel_ratio,
                   (target_size.height() - 2) * device_pixel_ratio),
            self.THUMBNAIL_CORNER_RADIUS * device_pixel_ratio,
            self.THUMBNAIL_CORNER_RADIUS * device_pixel_ratio,
        )
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.drawImage(int((target_size.width() * device_pixel_ratio -
                               scaled.width()) / 2),
                          0, scaled)

        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceOver)
        outline_color = QColor(255, 255, 255) if not is_new_map_thumbnail \
            else QColor(220, 220, 220)
        pen = QPen(outline_color)
        pen.setWidthF(self.BORDER_WIDTH_PIXELS * device_pixel_ratio)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            QRectF(device_pixel_ratio,
                   device_pixel_ratio,
                   (target_size.width() - 2) * device_pixel_ratio,
                   (target_size.height() - 2) * device_pixel_ratio),
            self.THUMBNAIL_CORNER_RADIUS * device_pixel_ratio,
            self.THUMBNAIL_CORNER_RADIUS * device_pixel_ratio,
        )

        painter.end()
        return im_out

    # QStyledItemDelegate interface
    # pylint: disable=missing-function-docstring,unused-argument
    def sizeHint(self, option, index):
        line_scale = 1
        if platform.system() == "Darwin":
            line_scale = 1.3

        return QSize(
            option.rect.width(),
            int(QFontMetrics(option.font).height() * 3 * line_scale),
        )

    # pylint: disable=too-many-locals
    def paint(
            self,
            painter: QPainter,
            option: QStyleOptionViewItem,
            index: QModelIndex
    ):
        self.initStyleOption(option, index)
        style = QApplication.style() if option.widget is None \
            else option.widget.style()

        device_pixel_ratio = 1.0 if option.widget is None else \
            option.widget.devicePixelRatioF()

        option.palette.setColor(QPalette.Highlight, self.SELECTED_ROW_COLOR)

        # draw background for item (i.e. selection background)
        style.drawPrimitive(
            QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        inner_rect = QRectF(option.rect)
        inner_rect.adjust(
            self.HORIZONTAL_MARGIN,
            self.VERTICAL_MARGIN,
            -self.HORIZONTAL_MARGIN,
            -self.VERTICAL_MARGIN,
        )

        thumbnail_width = int(inner_rect.height() *
                              RecentMapDelegate.THUMBNAIL_RATIO)

        thumbnail_image = index.data(RecentMapsModel.ThumbnailRole)
        is_new_map_index = index.data(RecentMapsModel.IsNewMapRole)

        if thumbnail_image and not thumbnail_image.isNull():
            scaled = self.process_thumbnail(
                thumbnail_image,
                int(inner_rect.height()),
                is_new_map_index,
                device_pixel_ratio
            )

            painter.drawImage(
                QRectF(
                    inner_rect.left(),
                    inner_rect.top(),
                    scaled.width() / device_pixel_ratio,
                    scaled.height() / device_pixel_ratio,
                ),
                scaled,
            )

        line_scale = 1
        if platform.system() == "Darwin":
            line_scale = 1.3

        font = QFont(option.font)
        metrics = QFontMetrics(font)
        font.setBold(False)
        painter.setFont(font)

        left_text_edge = (
                inner_rect.left() +
                thumbnail_width +
                self.HORIZONTAL_MARGIN * 2
        )

        line_heights = [1.0 * line_scale, 2.0 * line_scale]

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self.HEADING_COLOR))
        painter.drawText(
            QPointF(
                left_text_edge,
                inner_rect.top() + int(metrics.height() * line_heights[0]),
            ),
            index.data(RecentMapsModel.TitleRole),
        )

        sub_title = index.data(RecentMapsModel.SubTitleRole)
        if sub_title:
            painter.setPen(QPen(self.SUBHEADING_COLOR))
            painter.setFont(font)
            painter.drawText(
                QPointF(
                    left_text_edge,
                    inner_rect.top() + int(metrics.height() * line_heights[1]),
                ),
                sub_title
            )

        painter.restore()
    # pylint: enable=too-many-locals

    # pylint: enable=missing-function-docstring,unused-argument


class RecentMapsListView(QListView):
    """
    Custom list view for recent maps
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._model = RecentMapsModel(self)
        self.setModel(self._model)
        delegate = RecentMapDelegate(self)
        self.setItemDelegate(delegate)

        p = self.palette()
        p.setColor(QPalette.Base, QColor(255, 255, 255))
        self.setPalette(p)

        fm = QFontMetrics(self.font())
        self.setMinimumHeight(fm.height() * 12)

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._model.first_results_found.connect(self._on_first_results_found)
        self._model.no_results_found.connect(self._on_no_results_found)

    def set_filter_string(self, filter_string: str):
        """
        Sets a text filter for the view
        """
        self._model.set_filter_string(filter_string)
        if not filter_string:
            # when you clear the search the new map
            # option should get selected again
            self.selectionModel().select(
                self._model.index(0, 0),
                QItemSelectionModel.ClearAndSelect)

    def set_workspace_id(self, workspace_id: Optional[str]):
        """
        Sets the selected workspace ID to filter the view
        """
        self._model.set_workspace_id(workspace_id)
        # when you change the workspace the new map
        # option should get selected again
        self.selectionModel().select(
            self._model.index(0, 0),
            QItemSelectionModel.ClearAndSelect)

    def set_new_map_title(self, title: str):
        """
        Sets the title to use for the new map item
        """
        self._model.set_new_map_title(title)

    def _on_first_results_found(self):
        """
        Triggered when the first page of maps are fetched
        """

        # while you search, the first search result should be
        # selected so you can quickly hit enter
        if self._model.filter_string():
            self.selectionModel().select(
                self._model.index(1, 0),
                QItemSelectionModel.ClearAndSelect)

    def _on_no_results_found(self):
        """
        Triggered when no matching search results are found
        """

        # when no search results are found, the new map
        # option should get selected again
        self.selectionModel().select(
            self._model.index(0, 0),
            QItemSelectionModel.ClearAndSelect)


class RecentMapsWidget(QWidget):
    """
    Custom widget allowing users to select from recent maps
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        self._filter = QgsFilterLineEdit()
        self._filter.setShowSearchIcon(True)
        self._filter.setPlaceholderText(self.tr('Search maps...'))
        self._filter._additional_stylesheet = """
        QgsFilterLineEdit{ border-top: 1px solid #bdbdbd;
        border-right: 1px solid #bdbdbd;
        border-left: 1px solid #bdbdbd;
        border-bottom: none;
        border-top-right-radius: 2px;
        border-top-left-radius: 2px;
        border-bottom-right-radius: 0px;
        border-bottom-left-radius: 0px;
        }"""

        def _update_filter_stylesheet():
            # this widget removes the stylesheet on edits!
            self._filter.setStyleSheet(
                self._filter.styleSheet() +
                self._filter._additional_stylesheet)

        self._filter.valueChanged.connect(_update_filter_stylesheet)
        _update_filter_stylesheet()
        self._filter.setFixedHeight(
            int(QFontMetrics(self._filter.font()).height() * 1.5))
        vl.addWidget(self._filter)

        self._view = RecentMapsListView()
        self._view.setStyleSheet("""
                QListView {
                    border: 1px solid #bdbdbd;
                    border-top-right-radius: 0px;
                    border-top-left-radius: 0px;
                    border-bottom-right-radius: 2px;
                    border-bottom-left-radius: 2px;
                    background: white! important;
                    }
                QListView::item::selected {
                    background-color: #fed9e3;
                    }
                """)

        vl.addWidget(self._view, 1)
        self.setLayout(vl)

        self._filter.textChanged.connect(self._view.set_filter_string)

        self._view.selectionModel().select(
            self._view.model().index(0, 0),
            QItemSelectionModel.ClearAndSelect)

    def filter_line_edit(self) -> QgsFilterLineEdit:
        """
        Returns a reference to the filter search widget
        """
        return self._filter

    def set_new_map_title(self, title: str):
        """
        Sets the title to use for the new map item
        """
        self._view.set_new_map_title(title)

    def selected_map(self) -> Optional[Map]:
        """
        Returns the current selected map
        """
        return self._view.selectionModel().selectedIndexes()[0].data(
            RecentMapsModel.MapRole
        )

    def set_workspace_id(self, workspace_id: Optional[str]):
        """
        Sets the selected workspace ID to filter the list
        """
        self._view.set_workspace_id(workspace_id)
