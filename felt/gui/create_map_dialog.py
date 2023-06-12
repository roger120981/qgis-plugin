# -*- coding: utf-8 -*-
"""Felt Create Map dialog

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2022 by Nyall Dawson'
__date__ = '22/11/2022'
__copyright__ = 'Copyright 2022, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from typing import Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QWidget,
    QDialog,
    QDialogButtonBox
)

from .constants import (
    PRIVACY_POLICY_URL,
    TOS_URL
)
from .gui_utils import GuiUtils
from .authorization_manager import AUTHORIZATION_MANAGER

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('create_map.ui'))


class CreateMapDialog(QDialog, WIDGET):
    """
    Custom dialog for creating maps

    If the dialog is accepted then the authorization process should be
    started.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setupUi(self)

        self.button_box.button(QDialogButtonBox.Ok).setText(
            self.tr('Add to Felt')
        )
        self.button_box.button(QDialogButtonBox.Ok).clicked.connect(
            self.accept
        )
        self.button_box.button(QDialogButtonBox.Cancel).clicked.connect(
            self.reject
        )
        self.button_box.button(QDialogButtonBox.Cancel).setText(
            self.tr('Close')
        )

        self.footer_label.linkActivated.connect(self._link_activated)

        if AUTHORIZATION_MANAGER.user:
            self.label_user.setText(
                self.tr('Signed in as: {}').format(
                    AUTHORIZATION_MANAGER.user.name
                )
            )

    def _link_activated(self, link: str):
        """
        Called when a hyperlink is clicked in dialog labels
        """
        if link == 'privacy_policy':
            url = QUrl(PRIVACY_POLICY_URL)
        elif link == 'terms_of_use':
            url = QUrl(TOS_URL)
        else:
            return

        QDesktopServices.openUrl(url)