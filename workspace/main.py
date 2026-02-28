import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from Pygments import highlight
from Pygments.lexers import PythonLexer
from Pygments.formatters import TerminalFormatter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set the window title and size
        self.setWindowTitle('Retro AI Agent Window System')
        self.setGeometry(100, 100, 400, 300)  # x, y, width, height

        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Top Section: Divide into two sections for agent messages
        top_section_layout = QHBoxLayout()
        left_agent_message = QLabel('Agent 1 Messages')
        right_agent_message = QLabel('Agent 2 Messages')
        top_section_layout.addWidget(left_agent_message)
        top_section_layout.addWidget(right_agent_message)
        main_layout.addLayout(top_section_layout)

        # Bottom Section: Terminal Output
        self.terminal_output = QWidget()
        terminal_layout = QVBoxLayout(self.terminal_output)
        self.terminal_display = QLabel('Status Display goes here...')
        terminal_layout.addWidget(self.terminal_display)
        main_layout.addWidget(self.terminal_output, stretch=10)

        # Add buttons (optional for now, but you can add more later)
        button_1 = QPushButton('Start Agent')
        button_2 = QPushButton('Stop Agent')
        main_layout.addWidget(button_1)
        main_layout.addWidget(button_2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())