from PyQt5 import QtWidgets

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    label1 = QtWidgets.QLabel("Hello world: ")
    text_input = QtWidgets.QLineEdit("")
    text_input.textChanged[str].connect(lambda text: label1.setText("Hello world: " + text))

    inner_layout = QtWidgets.QHBoxLayout()
    label2 = QtWidgets.QLabel("Bonjour")
    inner_layout.addWidget(label2)

    outer_layout = QtWidgets.QVBoxLayout()
    outer_layout.addWidget(label1)
    outer_layout.addWidget(text_input)
    outer_layout.addLayout(inner_layout)

    window = QtWidgets.QWidget()
    window.setLayout(outer_layout)
    window.show()
    app.exec_()
