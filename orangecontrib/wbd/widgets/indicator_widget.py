"""Model with the main Orange Widget.

This module contains the world bank data widget, used for fetching data from
world bank data API.
"""

import sys
import signal
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import wbpy
import Orange
from Orange.data import table
from Orange.widgets import widget
from Orange.widgets import gui
from Orange.widgets.utils import concurrent
from orangecontrib.wbd.widgets import indicators_widget
from orangecontrib.wbd.widgets import countries_widget
from orangecontrib.wbd.widgets import timeframe_widget


logger = logging.getLogger(__name__)


class IndicatorAPI(widget.OWWidget):
    """World bank data widget for Orange."""

    # Widget needs a name, or it is considered an abstract widget
    # and not shown in the menu.
    name = "World Bank Data"
    icon = "icons/mywidget.svg"
    category = "Data"
    want_main_area = False
    outputs = [widget.OutputSignal(
        "Data", table.Table,
        doc="Attribute-valued data set read from the input file.")]

    def __init__(self):
        super().__init__()
        logger.debug("Initializing {}".format(self.__class__.__name__))

        self.api = wbpy.IndicatorAPI()
        layout = QtGui.QVBoxLayout()
        self.button = QtGui.QPushButton("Fetch Data")
        self.button.clicked.connect(self.fetch_button_clicked)

        self.countries = countries_widget.CountriesWidget()
        self.indicators = indicators_widget.IndicatorsListWidget()
        self.timeframe = timeframe_widget.TimeFrameWidget()
        layout.addWidget(self.indicators)
        layout.addWidget(self.countries)
        layout.addWidget(self.timeframe)
        layout.addWidget(self.button)
        layout.setAlignment(QtCore.Qt.AlignTop)

        self._executor = concurrent.ThreadExecutor(
            threadPool=QtCore.QThreadPool(maxThreadCount=2)
        )
        self._task = concurrent.Task(function=self._delay)
        self._task.resultReady.connect(self._delay_completed)
        self._task.exceptionReady.connect(self._delay_exception)
        self._executor.submit(self._task)

        gui.widgetBox(self.controlArea, margin=0, orientation=layout)

    def _delay(self):
        logger.debug("delay start")
        import time
        time.sleep(4)
        logger.debug("eraly bidr")

    def _delay_exception(self):
        logger.debug("delay exception")

    def _delay_completed(self):
        logger.debug("delay copmleted")

    def fetch_button_clicked(self):
        """Fetch button clicked for wbd.

        Retrieve and display the response from world bank data if the
        indicator, countries and dates have been properly set for a valid
        query.
        """
        logger.debug("Fetch indicator data")
        indicator = self.indicators.get_indicator()
        countries = self.countries.get_counries()
        timeframe = self.timeframe.get_timeframe()

        logger.debug(indicator)
        logger.debug(countries)
        logger.debug(timeframe)
        dataset = self.api.get_dataset(indicator, country_codes=countries,
                                       **timeframe)
        data_list = dataset.as_list(use_datetime=True)
        self.send_data(data_list)

    def data_updated(self, data_list):
        self.send_data(data_list)

    def send_data(self, data):

        if data[0][0] == "Date":
            first_column = Orange.data.TimeVariable("Date")
            for row in data[1:]:

                logger.debug(row)
                logger.debug(row[0].isoformat())
                row[0] = first_column.parse(row[0].isoformat())
        elif data[0][0] == "Country":
            first_column = Orange.data.StringVariable("Country")

        logger.debug(data)

        domain_columns = [first_column] + [
            Orange.data.ContinuousVariable(column_name)
            for column_name in data[0][1:]
        ]

        domain = Orange.data.Domain(domain_columns)

        data = Orange.data.Table(domain, data[1:])

        self.send("Data", data)

    def keyPressEvent(self, event):
        """Capture and ignore all key press events.

        This is used so that return key event does not trigger the exit button
        from the dialog. We need to allow the return key to be used in filters
        in the widget."""
        pass


def main():  # pragma: no cover
    """Helper for running the widget without Orange."""
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)
    orange_widget = IndicatorAPI()
    orange_widget.show()
    app.exec_()
    orange_widget.saveSettings()


if __name__ == "__main__":
    main()
