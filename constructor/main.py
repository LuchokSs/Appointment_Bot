import json
import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLayout
from PyQt5 import uic


SOURCE = 'bots.json'


class BotWidget(QWidget):
    def __init__(self,
                 parent,
                 index,
                 medorg_id,
                 medorg_name,
                 telegram_token,
                 r_interval,
                 c_timeout,
                 cell_number_limit
                 ):
        super().__init__()
        uic.loadUi('interface/bot_widget.ui', self)

        self.id_input.setText(str(medorg_id))
        self.name_input.setText(medorg_name)
        self.token_input.setText(telegram_token)

        self.reminder_interval_input.setValue(r_interval[0])
        self.reminder_interval_mult.addItem('часы')
        self.reminder_interval_mult.addItem('секунды')
        self.reminder_interval_mult.addItem('минуты')
        self.reminder_interval_mult.setCurrentIndex(
            0 if r_interval[1] == 'часы' else (1 if r_interval[1] == 'секунды' else 2))
        self.current_reminder_mult = r_interval[1]
        self.reminder_interval_mult.currentTextChanged.connect(self.interval_changed)

        self.conversation_timeout_input.setValue(c_timeout[0])
        self.conversation_timeout_mult.addItem('часы')
        self.conversation_timeout_mult.addItem('секунды')
        self.conversation_timeout_mult.addItem('минуты')
        self.conversation_timeout_mult.setCurrentIndex(
            0 if c_timeout[1] == 'часы' else (1 if c_timeout[1] == 'секунды' else 2))
        self.current_timeout_mult = c_timeout[1]
        self.conversation_timeout_mult.currentTextChanged.connect(self.timeout_changed)

        self.cell_number_limit.setValue(cell_number_limit)

        self.delete_button.clicked.connect(parent.delete_bot)
        self.delete_button.index = index

    def interval_changed(self, interval):
        self.current_reminder_mult = interval

    def timeout_changed(self, timeout):
        self.current_timeout_mult = timeout


class Application(QMainWindow):
    def __init__(self):
        self.bots = []
        super().__init__()
        uic.loadUi('interface/main_window.ui', self)
        self.create_bot_button.clicked.connect(self.create_bot)
        self.save_button.clicked.connect(self.save_bots)

        self.update_bots()

    def create_bot(self,
                   empty,
                   medorg_id='1',
                   medorg_name='Test',
                   telegram_token=None,
                   r_interval=(30, 'минуты'),
                   c_timeout=(15, "минуты"),
                   cell_number_limit=21
                   ):
        self.bots.append(BotWidget(self,
                                   len(self.bots) - 1,
                                   medorg_id=medorg_id,
                                   medorg_name=medorg_name,
                                   telegram_token=telegram_token,
                                   r_interval=r_interval,
                                   c_timeout=c_timeout,
                                   cell_number_limit=cell_number_limit))
        self.verticalLayout.addWidget(self.bots[-1])

    def update_bots(self):
        with open(SOURCE) as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                return
        for bot in data:
            self.create_bot(None,
                            bot['medorg_id'],
                            bot['medorg_name'],
                            bot['telegram_token'],
                            bot['r_interval'],
                            bot['c_timeout'],
                            bot['cell_number_limit'])

    def save_bots(self):
        data = []
        for bot in self.bots:
            bot_config = {'medorg_id': bot.id_input.text(),
                          'medorg_name': bot.name_input.text(),
                          'telegram_token': bot.token_input.text(),
                          'r_interval': (bot.reminder_interval_input.value(), bot.current_reminder_mult),
                          'c_timeout': (bot.conversation_timeout_input.value(), bot.current_timeout_mult),
                          'cell_number_limit': bot.cell_number_limit.value()}
            data.append(bot_config)
        with open(SOURCE, 'w') as file:
            json.dump(data, file)

    def delete_bot(self):
        self.verticalLayout.removeWidget(self.bots[self.sender().index])
        del self.bots[self.sender().index]


if __name__ == '__main__':
    beg = QApplication(sys.argv)
    app = Application()
    app.show()
    sys.exit(beg.exec())
