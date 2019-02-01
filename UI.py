from __future__ import unicode_literals
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtWidgets import QMessageBox, QProgressBar
from winreg import *
import json
import getpass
import re
import youtube_dl
import ffmpeg
import sys
import random
import os


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # Parameter Lists and condition checking
        self.videoFormats = ["mp4", "3gp", "flv", "webm"]
        self.audioFormats = ["mp3", "m4a", "ogg", "wav", "aac"]
        self.qualityOptions = ["best", "worst"]
        self.currentSelection = "Video"
        # Youtube-dl command arg values
        self.URL = ""
        self.selectedFormat = "mp4"
        self.quality = self.qualityOptions[0]
        self.outputDir = "~/Downloads"
        if os.name == 'nt':
            with OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
                self.outputDir = QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                self.outputDir = self.outputDir.replace(os.sep, "/") + "/"

        self.setWindowTitle("Youtube-DL Manager")

        # UI items
        # Youtube Link
        self.lblYTLink = QtWidgets.QLineEdit()
        self.lblYTLink.setPlaceholderText("Youtube Video/Playlist Here...")
        # Output location
        self.lblOutputDir = QtWidgets.QLineEdit()
        self.lblOutputDir.setPlaceholderText("Output Directory...")
        self.lblOutputDir.setText(self.outputDir)
        self.dirFinder = QtWidgets.QPushButton("Output Directory")
        # Overall File Format (radio button - radioFormatAudio/Video) and Specific format (combo box - cmbFormatList)
        self.radioFormatVideo = QtWidgets.QRadioButton("Video")
        self.radioFormatVideo.setChecked(True)
        self.radioFormatAudio = QtWidgets.QRadioButton("Audio")
        self.cmbFormatList = QtWidgets.QComboBox()
        self.cmbFormatList.addItems(self.videoFormats)
        self.cmbQuality = QtWidgets.QComboBox()
        self.cmbQuality.addItems(self.qualityOptions)
        # Push download request
        self.btnDownload = QtWidgets.QPushButton("Download")
        self.progressState = QtWidgets.QLabel("Status: Inactive")

        # Set onClick methods
        self.btnDownload.clicked.connect(self.download_link)
        self.dirFinder.clicked.connect(self.get_out_dir)
        self.radioFormatVideo.toggled.connect(lambda: self.format_state(self.radioFormatVideo))
        self.radioFormatAudio.toggled.connect(lambda: self.format_state(self.radioFormatAudio))
        self.cmbFormatList.currentIndexChanged.connect(self.file_type_change)
        self.cmbQuality.currentIndexChanged.connect(self.quality_type_changed)
        self.lblYTLink.textChanged.connect(self.link_changed)
        self.lblOutputDir.textChanged.connect(self.outdir_changed)

        # Layouts
        self.layout = QtWidgets.QVBoxLayout()
        self.linkWidgets = QtWidgets.QVBoxLayout()
        self.outputWidgets = QtWidgets.QHBoxLayout()
        self.formatWidgets = QtWidgets.QHBoxLayout()
        self.downloadWidgets = QtWidgets.QHBoxLayout()
        self.statusWidgets = QtWidgets.QHBoxLayout()
        # Widgets
        self.linkWidgets.addWidget(self.lblYTLink)
        self.outputWidgets.addWidget(self.lblOutputDir)
        self.outputWidgets.addWidget(self.dirFinder)
        self.formatWidgets.addWidget(self.radioFormatVideo)
        self.formatWidgets.addWidget(self.radioFormatAudio)
        self.formatWidgets.addWidget(self.cmbFormatList)
        self.formatWidgets.addWidget(self.cmbQuality)
        self.downloadWidgets.addStretch()
        self.downloadWidgets.addWidget(self.btnDownload)
        self.statusWidgets.addWidget(self.progressState)
        # Vertically append layouts to self.layout
        self.layout.addLayout(self.linkWidgets)
        self.layout.addLayout(self.outputWidgets)
        self.layout.addLayout(self.formatWidgets)
        self.layout.addLayout(self.downloadWidgets)
        self.layout.addLayout(self.statusWidgets)
        self.setLayout(self.layout)

    def download_link(self):
        checkDrive = re.match("[a-z,A-Z]:/*", self.outputDir)
        if self.outputDir:
            if checkDrive:
                if not os.path.exists(self.outputDir):
                    try:
                        os.makedirs(self.outputDir)
                    except OSError as e:
                        if e.errno != e.errno.EEXIST:
                            self.msg_warning("Invalid Directory",
                                             "Could not create new directory at location: " + self.outputDir)
                            raise
                self.pass_command()
            else:
                self.msg_warning("Bad Directory Input",
                                 "Invalid directory input.\nPlease make sure it is a location on one of your drives")
        else:
            self.msg_warning("Empty Directory Inputted",
                             "Empty Directory, please find an output folder")

    def pass_command(self):
        self.btnDownload.setEnabled(False)
        self.ydl_opts = {
            'format': self.quality,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'outtmpl': self.outputDir + '%(title)s-%(id)s.%(ext)s'
        }
        if self.currentSelection == "Audio":
            self.ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.selectedFormat,
                'preferredquality': '192',
            }]
        elif self.currentSelection == "Video":
            self.ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': self.selectedFormat
            }]
        self.ydl_opts['progress_hooks'] = [self.yt_dl_hook]
        self.checkPlaylist = re.match("^.*(youtu.be\/|list=)([^#\&\?]*).*", self.URL)
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            if self.checkPlaylist:
                self.update_status("Getting playlist data...")
                playlist_dict = ydl.extract_info(self.URL, download=False)
                URL_LIST = []
                for entry in playlist_dict['entries']:
                    URL_LIST.append(entry['webpage_url'])
                print(URL_LIST)
                i = 1
                for URL in URL_LIST:
                    self.update_status("Downloading " + str(i) + "/" + str(len(URL_LIST)))
                    ydl.download([URL])
                    i += 1

            elif not self.checkPlaylist:
                self.update_status("Downloading...")
                ydl.download([self.URL])
            self.update_status("Downloading Complete")
        self.btnDownload.setEnabled(True)
        self.btnDownload.setDisabled(False)

    def update_status(self, status_text):
            self.progressState.setText(status_text)
            self.progressState.adjustSize()
            QtGui.QGuiApplication.processEvents()

    def yt_dl_hook(self, d):
        if d['status'] == 'finished':
            file_tuple = os.path.split(os.path.abspath(d['filename']))
            self.update_status("Done processing {}".format(file_tuple[1]))

    def msg_warning(self, title="Error occurred", message="User error occurred"):
        warning = QMessageBox()
        warning.setStandardButtons(QMessageBox.Ok)
        warning.setWindowTitle(title)
        warning.setText(message)
        warning.exec_()

    def get_out_dir(self):
        self.outputDir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Output Folder', 'c:\\') + "/"
        self.lblOutputDir.setText(self.outputDir)

    def link_changed(self, text):
        self.URL = text

    def outdir_changed(self, text):
        self.outputDir = text

    def quality_type_changed(self, i):
        self.quality = self.qualityOptions[i]

    def file_type_change(self, i):
        if self.currentSelection == "Video":
            self.selectedFormat = self.videoFormats[i]
        elif self.currentSelection == "Audio":
            self.selectedFormat = self.audioFormats[i]

    def format_state(self, b):
        if b.text() == "Video":
            if b.isChecked():
                self.currentSelection = "Video"
                self.cmbFormatList.clear()
                self.cmbFormatList.addItems(self.videoFormats)

        if b.text() == "Audio":
            if b.isChecked():
                self.currentSelection = "Audio"
                self.cmbFormatList.clear()
                self.cmbFormatList.addItems(self.audioFormats)
