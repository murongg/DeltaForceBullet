import logging
import sys
import threading
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QCoreApplication
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor


class LogEmitter(QObject):
    """Qt日志信号发射器（确保在主线程初始化）"""
    new_log = pyqtSignal(str, str)  # (原始消息, HTML格式消息)


class QtLogger(logging.Logger):
    """支持Qt GUI输出的日志器"""

    def __init__(self, name: str):
        super().__init__(name)
        # 确保emitter在主线程创建
        if QCoreApplication.instance():
            self.emitter = LogEmitter()
        else:
            raise RuntimeError("必须先初始化QApplication")

        self._init_colors()
        self.lock = threading.RLock()

    def _init_colors(self):
        """定义日志级别颜色"""
        self.qt_colors = {
            logging.DEBUG: ("#666666", "DEBUG"),
            logging.INFO: ("#000000", "INFO"),
            logging.WARNING: ("#FF8000", "WARN"),
            logging.ERROR: ("#FF0000", "ERROR"),
            logging.CRITICAL: ("#8B0000", "CRITICAL")
        }

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func, extra, sinfo):
        """创建增强版LogRecord"""
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        # 添加GUI需要的颜色信息
        record.qt_color, record.qt_level = self.qt_colors.get(
            level, ("#000000", "UNKNOWN")
        )
        return record

    def handle(self, record):
        """处理日志记录"""
        with self.lock:
            # 执行标准日志处理
            super().handle(record)

            # 准备GUI输出
            html_msg = (
                f"<span style='color:{record.qt_color};'>"
                f"[{record.qt_level}] {record.getMessage()}"
                "</span>"
            )
            # 发送信号（使用队列连接确保线程安全）
            self.emitter.new_log.emit(
                record.getMessage(),
                html_msg
            )


class LogDisplayController(QObject):
    """连接日志器和GUI显示的核心控制器"""

    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit
        self.setup_connections()

    def setup_connections(self):
        """建立信号连接"""
        app_logger = logging.getLogger("app")
        if isinstance(app_logger, QtLogger):
            # 使用队列连接确保跨线程安全
            app_logger.emitter.new_log.connect(
                self.append_log,
                Qt.ConnectionType.QueuedConnection
            )
        else:
            raise TypeError("日志器必须是QtLogger实例")

    def append_log(self, raw_msg: str, html_msg: str):
        """线程安全的日志追加方法"""
        try:
            # 确保在UI线程执行
            if QCoreApplication.instance().thread() != self.thread():
                raise RuntimeError("必须在主线程操作UI")

            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)

            max_lines = 1000
            current_line_count = self.text_edit.document().lineCount()
            if current_line_count >= max_lines:
                # 计算需要删除的行数（保留最后 max_lines-1 行）
                lines_to_remove = current_line_count - max_lines + 1
                keep_cursor = self.text_edit.textCursor()
                keep_cursor.movePosition(QTextCursor.Start)
                # 选择前 N 行进行删除
                keep_cursor.movePosition(
                    QTextCursor.Down,
                    QTextCursor.KeepAnchor,
                    n=lines_to_remove
                )
                keep_cursor.removeSelectedText()

            cursor.insertHtml(f"{html_msg}<br>")

            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            sys.stderr.write(f"日志显示失败: {str(e)}\n")


# 初始化示例
def configure_log_system():
    # 配置日志器（必须在QApplication之后调用）
    logging.setLoggerClass(QtLogger)
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    # 文件处理器
    file_handler = logging.FileHandler("app.log", encoding='utf-8')
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger