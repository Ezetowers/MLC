# -*- coding: utf-8 -*-

import numpy as np
import os
import random
import sys
sys.path.append(os.path.abspath(".") + "/../..")

from MLC.GUI.Experiment.QtCharts.QtChartWrapper import QtChartWrapper
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ChartConfiguration():
    CHART_COLORS = {"White": Qt.white,
                    "Black": Qt.black,
                    "Red": Qt.red,
                    "DarkRed": Qt.darkRed,
                    "Green": Qt.green,
                    "DarkGreen": Qt.darkGreen,
                    "Blue": Qt.blue,
                    "DarkBlue": Qt.darkBlue,
                    "Cyan": Qt.cyan,
                    "DarkCyan": Qt.darkCyan,
                    "Magenta": Qt.magenta,
                    "DarkMagenta": Qt.darkMagenta,
                    "Yellow": Qt.yellow,
                    "DarkYellow": Qt.darkYellow,
                    "Gray": Qt.gray,
                    "DarkGray": Qt.darkGray,
                    "LightGray": Qt.lightGray}

    # Min, Max, Step
    AMOUNT_POINTS = [100, 1000, 100]
    MAX_COST_VALUES = [50, 1000, 50]
    MIN_COST_VALUES = [-200, 0, 50]
    MARKER_SIZE_VALUES = [1, 10, 1]

    def __init__(self, autogenerated_object):
        self._autogenerated_object = autogenerated_object
        self._min_cost_combo = self._autogenerated_object.min_cost_combo
        self._max_cost_combo = self._autogenerated_object.max_cost_combo
        self._nan_color_combo = self._autogenerated_object.nan_color_combo
        self._nan_value_combo = self._autogenerated_object.nan_value_combo
        self._overflow_color_combo = self._autogenerated_object.overflow_color_combo
        self._overflow_value_combo = self._autogenerated_object.overflow_value_combo
        self._valid_points_combo = self._autogenerated_object.valid_points_combo
        self._marker_combo = self._autogenerated_object.marker_combo
        self._points_combo = self._autogenerated_object.points_combo

    def init(self):
        # Variable used to determine when the chart can be updated
        self._update_chart = False
        # Load the colors in the combos
        self._overflow_color_combo.addItems([key for key, value in ChartConfiguration.CHART_COLORS.iteritems()])
        self._valid_points_combo.addItems([key for key, value in ChartConfiguration.CHART_COLORS.iteritems()])
        self._nan_color_combo.addItems([key for key, value in ChartConfiguration.CHART_COLORS.iteritems()])
        self._max_cost_combo.addItems([str(x) for x in xrange(ChartConfiguration.MAX_COST_VALUES[0],
                                                              ChartConfiguration.MAX_COST_VALUES[1] +
                                                              ChartConfiguration.MAX_COST_VALUES[2],
                                                              ChartConfiguration.MAX_COST_VALUES[2])])
        self._min_cost_combo.addItems([str(x) for x in xrange(ChartConfiguration.MIN_COST_VALUES[0],
                                                              ChartConfiguration.MIN_COST_VALUES[1] +
                                                              ChartConfiguration.MIN_COST_VALUES[2],
                                                              ChartConfiguration.MIN_COST_VALUES[2])])
        self._marker_combo.addItems([str(x) for x in xrange(ChartConfiguration.MARKER_SIZE_VALUES[0],
                                                            ChartConfiguration.MARKER_SIZE_VALUES[1] +
                                                            ChartConfiguration.MARKER_SIZE_VALUES[2],
                                                            ChartConfiguration.MARKER_SIZE_VALUES[2])])
        self._points_combo.addItems([str(x) for x in xrange(ChartConfiguration.AMOUNT_POINTS[0],
                                                            ChartConfiguration.AMOUNT_POINTS[1] +
                                                            ChartConfiguration.AMOUNT_POINTS[2],
                                                            ChartConfiguration.AMOUNT_POINTS[2])])
        self._set_defaults()
        self._create_new_chart()
        self._update_chart = True

    def update_chart(self):
        if self._update_chart:
            self._set_default_overflow_and_nan_values()
            self._create_new_chart()

    def chart_params(self):
        chart_params = {"max_cost": int(self._max_cost_combo.currentText()),
                        "min_cost": int(self._min_cost_combo.currentText()),
                        "marker_size": int(self._marker_combo.currentText()),
                        "overflow_value": int(self._overflow_value_combo.currentText()),
                        "nan_value": int(self._nan_value_combo.currentText()),
                        "valid_points_color": ChartConfiguration.CHART_COLORS[self._valid_points_combo.currentText()],
                        "overflow_color": ChartConfiguration.CHART_COLORS[self._overflow_color_combo.currentText()],
                        "nan_color": ChartConfiguration.CHART_COLORS[self._nan_color_combo.currentText()]}
        return chart_params

    def _set_defaults(self):
        self._min_cost_combo.setCurrentIndex(0)
        self._max_cost_combo.setCurrentIndex(self._max_cost_combo.count() - 1)
        self._marker_combo.setCurrentIndex(self._marker_combo.count() / 2 - 1)
        self._points_combo.setCurrentIndex(0)
        self._valid_points_combo.setCurrentIndex(int(self._valid_points_combo.findText("DarkGreen")))
        self._overflow_color_combo.setCurrentIndex(int(self._overflow_color_combo.findText("Red")))
        self._nan_color_combo.setCurrentIndex(int(self._nan_color_combo.findText("Magenta")))
        self._refresh_overflow_and_nan_combos()

    def _set_default_overflow_and_nan_values(self):
        min_cost_value = int(self._min_cost_combo.currentText())
        overflow_min_value = int(self._overflow_value_combo.itemText(0))
        nan_min_value = int(self._nan_value_combo.itemText(0))

        # Deactivate the chart updating to avoid recursion problems
        self._update_chart = False
        self._refresh_overflow_and_nan_combos()

        # Activate it again
        # FIXME: There should be a better option than this
        self._update_chart = True

    def _refresh_overflow_and_nan_combos(self):
        min_cost_value = int(self._min_cost_combo.currentText())
        # The first time the combos are loaded there is no value in the combos.
        # In that case, use the min_cost_value as default
        overflow_value = None
        nan_value = None
        try:
            overflow_value = int(self._overflow_value_combo.currentText())
            nan_value = int(self._nan_value_combo.currentText())
        except ValueError:
            overflow_value = min_cost_value
            nan_value = min_cost_value

        overflow_and_nan_step = ChartConfiguration.MIN_COST_VALUES[2]
        self._overflow_value_combo.clear()
        self._overflow_value_combo.addItems([str(x) for x in xrange(min_cost_value,
                                                                    ChartConfiguration.MIN_COST_VALUES[1] +
                                                                    overflow_and_nan_step,
                                                                    overflow_and_nan_step)])

        self._nan_value_combo.clear()
        self._nan_value_combo.addItems([str(x) for x in xrange(min_cost_value,
                                                               ChartConfiguration.MIN_COST_VALUES[1] +
                                                               overflow_and_nan_step,
                                                               overflow_and_nan_step)])
        if min_cost_value < overflow_value:
            self._overflow_value_combo.setCurrentIndex(
                self._overflow_value_combo.findText(str(overflow_value)))

        if min_cost_value < nan_value:
            self._nan_value_combo.setCurrentIndex(
                self._nan_value_combo.findText(str(nan_value)))

    def _create_new_chart(self):
        # Insert the widget into the widget
        chart_conf_layout = self._autogenerated_object.chart_conf_layout

        chart_title = 'Generation {0} - Cost Per Individual'.format(1)
        chart_font = QFont()
        chart_font.setWeight(QFont.ExtraBold)
        indiv_chart = QtChartWrapper(show_legend=True)
        indiv_chart.set_title(chart_title, chart_font)
        indiv_chart.set_object_name("chart_conf")

        # Set the object name to be able to retrieve it later
        indiv_chart.set_xaxis(log=False, label="Individuals",
                              label_format='%i', tick_count=10)
        indiv_chart.set_yaxis(log=False, label="Costs",
                              label_format='%g', tick_count=11)

        valid_points_color = ChartConfiguration.CHART_COLORS[self._valid_points_combo.currentText()]
        overflow_color = ChartConfiguration.CHART_COLORS[self._overflow_color_combo.currentText()]
        nan_color = ChartConfiguration.CHART_COLORS[self._nan_color_combo.currentText()]

        marker_size = int(self._marker_combo.currentText())
        # Blue: Valid points
        indiv_chart.add_scatter(marker_size=marker_size, color=valid_points_color, legend="Valid Points")
        # Red: Overflow points
        indiv_chart.add_scatter(marker_size=marker_size, color=overflow_color, legend="Overflow")
        # Yellow: Nan and Inf points
        indiv_chart.add_scatter(marker_size=marker_size, color=nan_color, legend="Nan or Inf")

        amount_points = int(self._points_combo.currentText())
        indiv_canvas = indiv_chart.get_widget()
        indiv_canvas.chart().axisX().setRange(1, amount_points)

        min_range = int(self._min_cost_combo.currentText())
        max_range = int(self._max_cost_combo.currentText())
        indiv_canvas.chart().axisY().setRange(min_range, max_range)
        self._max_cost = 0

        # Add Points
        for index in xrange(1, amount_points + 1):
            if index % 11 == 0:
                # Add an overflow point every 11 points
                overflow_value = int(self._overflow_value_combo.currentText())
                indiv_chart.append_point(1, index, overflow_value)
            elif index % 17 == 0:
                # Add a nan point every 17 points
                nan_value = int(self._nan_value_combo.currentText())
                indiv_chart.append_point(2, index, nan_value)
            else:
                # Draw a cosine
                amp = max_range / 2
                value = amp * np.cos(2 * np.pi * index / amount_points) + amp
                indiv_chart.append_point(0, index, value)

        # Remove all previous widgets before rendering again
        for i in reversed(range(chart_conf_layout.count())):
            chart_conf_layout.itemAt(i).widget().setParent(None)

        # Add the Chart Conf Canvas
        chart_conf_layout.addWidget(indiv_canvas)
