import sys
import requests
from PyQt5.QtWidgets import QTextBrowser, QApplication, QWidget, QMessageBox, QProgressBar, QGridLayout, QTextEdit, QPushButton, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt


class SpellCheckThread(QThread):

    add = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, txt):
        QThread.__init__(self)
        self.txt = txt

    def __del__(self):
        self.wait()

    def check(self, txt):
        url = 'https://m.search.naver.com/p/csearch/ocontent/util/SpellerProxy'
        params = {'q': txt
            , 'where': 'nexearch'
            , 'color_blindness': 0}

        result = requests.get(url, params=params).json()
        checked = result['message']['result']['html']
        checked = checked.replace('class=\'', 'style="color:')
        checked = checked.replace('_text\'', '"')
        checked = checked.replace('em', 'b')
        checked = checked.replace('color:green', 'color:#03CF5D')
        checked = checked.replace('color:violet', 'color:#B22AF8')
        return checked

    def run(self):
        tmp = ''
        for i, ch in enumerate(self.txt, 1):
            if ch not in '.!?' and ch != '\n':
                tmp += ch
            else:
                tmp += ch
                if len(tmp.rstrip()) > 0:
                    result = self.check(tmp)
                    self.add.emit(result + ' ')
                else:
                    self.add.emit('<br>')
                tmp = ''
            self.progress.emit(i)
        if len(tmp) > 0:
            self.add.emit(self.check(tmp) + ' ')


class SpellCheckApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('맞춤법 검사기')
        self.resize(600, 300)
        self.setWindowIcon(QIcon('pencil.png'))

        self.setStyleSheet(
            'QPushButton{border-radius: 5px; border: 1px solid #ccc;'
            'padding: 5px; background-color:white; color: #555;}'
            'QPushButton:pressed{background-color:#ccc;}'
            'QPushButton:flat{background-color:#03cf5d; color:white; font-weight:bold;}'
            'QTextEdit{padding:5px; border-radius:5px; border: 1px solid #ccc;'
            'background-color:white; color: #555;}'
            'QProgressBar{border: 1px solid #ccc; padding: 2px;'
            'border-radius: 5px; text-align:center; font-weight:bold;'
            'background-color:white; color:#333;}'
            'QProgressBar::chunk{background-color:#03CF5D;'
            'border-radius:5px;}')

        grid = QGridLayout()

        self.check = QPushButton('검사', self)
        self.check.clicked.connect(self._check_)
        self.clear = QPushButton('초기화', self)
        self.clear.clicked.connect(self.clear_all)
        self.load = QPushButton('불러오기', self)
        self.load.clicked.connect(self.open_file)
        self.save = QPushButton('저장', self)
        self.save.clicked.connect(self.save_file)
        self.top = QPushButton('항상 위', self)
        self.top.clicked.connect(self.allways_top)
        self.origin = QTextEdit()
        self.origin.setAcceptRichText(False)
        self.origin.setPlaceholderText('검사할 내용을 작성하거나 텍스트 파일을 불러오세요.')
        self.checked = QTextBrowser()
        self.copy = QPushButton('복사', self)
        self.copy.clicked.connect(self._copy_)
        self.checked.setToolTip('<b><p style="color:red">맞춤법</p>'
                                '<p style="color:#B22AF8">표준어 의심</p>'
                                '<p style="color:#03CF5D">띄어쓰기</p>'
                                '<p style="color:blue">통계적 교정</p></b>')
        self.checked.setAcceptRichText(True)
        self.checked.setReadOnly(True)
        self.pb = QProgressBar()

        grid.addWidget(self.load, 0, 0)
        grid.addWidget(self.check, 0, 1)
        grid.addWidget(self.clear, 0, 2)
        grid.addWidget(self.save, 0, 3)
        grid.addWidget(self.copy, 0, 4)
        grid.addWidget(self.top, 0, 5)

        grid.addWidget(self.origin, 1, 0, 1, 3)
        grid.addWidget(self.checked, 1, 3, 1, 3)
        grid.addWidget(self.pb, 2, 0, 1, 6)

        self.setLayout(grid)

        self.show()

    def open_file(self):
        file_name = QFileDialog.getOpenFileName(self, 'Open', '', 'Text Files(*.txt);; All Files(*)', '')
        if file_name[0]:
            self.clear_all()
            with open(file_name[0], 'r', encoding='utf8') as f:
                lines = f.readlines()
                for line in lines:
                    self.origin.append(line)

    def clear_all(self):
        self.origin.clear()
        self.checked.clear()

    def _check_(self):
        txt = self.origin.toPlainText()
        self.checked.clear()

        self.pb.setMaximum(len(txt))

        self.get_thread = SpellCheckThread(txt)
        self.get_thread.progress.connect(self.get_progress_value)
        self.get_thread.add.connect(self.add)
        self.get_thread.start()
        self.checked.setEnabled(False)

    def save_file(self):
        file_name = QFileDialog.getSaveFileName(self, 'Save', '', 'Text File(*.txt);; All File(*)', '')
        if file_name[0]:
            with open(file_name[0], 'w', encoding='utf8') as f:
                lines = self.checked.toPlainText()
                f.writelines(lines)
                QMessageBox.about(self, 'Saved', file_name[0] + '에 저장했습니다.')

    def allways_top(self):
        if self.top.isFlat():
            self.top.setFlat(False)
            self.setWindowFlags(self.windowFlags() & ~ Qt.WindowStaysOnTopHint)
        else:
            self.top.setFlat(True)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()

    def _copy_(self):
        self.checked.selectAll()
        self.checked.copy()

    @pyqtSlot(str)
    def add(self, txt):
        self.checked.insertHtml(txt)

    @pyqtSlot(int)
    def get_progress_value(self, val):
        self.pb.setValue(val)
        if val == self.pb.maximum():
            self.checked.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SpellCheckApp()
    sys.exit(app.exec_())
