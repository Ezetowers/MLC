# -*- coding: utf-8 -*-

import os
import numpy as np
import sys
sys.path.append(os.path.abspath(".") + "/../..")

from MLC.Log.log import get_gui_logger
from MLC.GUI.Autogenerated.autogenerated import Ui_Experiment
from MLC.GUI.Experiment.MatplotlibCanvas.CostPerIndividualCanvas import CostPerIndividualCanvas
from MLC.GUI.Experiment.QtCharts.QtChartWrapper import QtChartWrapper
from MLC.GUI.Experiment.ExperimentInProgressDialog import ExperimentInProgressDialog
from MLC.GUI.Tables.ConfigDictTableModel import ConfigDictTableModel
from MLC.GUI.Tables.ConfigTableModel import ConfigTableModel
from MLC.individual.Individual import Individual
from MLC.Common.Lisp_Tree_Expr import Lisp_Tree_Expr
from MLC.Population.Evaluation.EvaluatorFactory import EvaluatorFactory
from MLC.Population.Population import Population
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox

logger = get_gui_logger()


class ExperimentDialog(QMainWindow):
    MAX_GENERATIONS = 30

    def __init__(self, parent, mlc_local, experiment_name):
        QMainWindow.__init__(self, parent)
        self._autogenerated_object = Ui_Experiment()
        self._autogenerated_object.setupUi(self)

        # Experiment tab parameters
        self._current_gen = 0

        # Open the experiment
        self._mlc_local = mlc_local
        self._experiment_name = experiment_name
        self.setWindowTitle("Experiment {0}".format(self._experiment_name))

        self._mlc_local.open_experiment(self._experiment_name)
        self._load_experiment_config()
        self._update_individuals_per_generation_list()
        self._update_experiment_info()
        self._update_individuals_figure()

        # Disable save_config_button until some change is made
        self._autogenerated_object.save_config_button.setDisabled(True)

    def closeEvent(self, event):
        logger.debug('[EXPERIMENT {0}] [CLOSE_DIALOG] - Executing overriden closeEvent function'.format(self._experiment_name))
        self._ask_if_experiment_config_must_be_saved()
        # Close the experiment
        self._mlc_local.close_experiment(self._experiment_name)

    def on_start_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [START_BUTTON] - Executing on_start_button_clicked function'.format(self._experiment_name))
        from_gen = int(self._autogenerated_object.from_gen_combo.currentText())
        to_gen = int(self._autogenerated_object.to_gen_combo.currentText())

        logger.info('[EXPERIMENT {0}] [START_BUTTON] - Proceed to execute experiment from Generation '
                    'N°{1} to Generation N°{2}'.format(self._experiment_name, from_gen, to_gen))
        self._mlc_local.go(self._experiment_name, to_gen, from_gen - 1)

        QMessageBox.information(self, 'Experiment executed', 'Experiment was succesfully executed.', QMessageBox.Ok)

        self._update_individuals_per_generation_list()
        self._update_experiment_info()
        self._update_individuals_figure()

        progress_dialog = ExperimentInProgressDialog(self)
        progress_dialog.exec_()

    def on_prev_gen_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [PREV_GEN_BUTTON] - Executing on_prev_gen_button_clicked function'.format(self._experiment_name))
        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        number_of_gens = experiment_info["generations"]

        if self._current_gen > 1:
            self._current_gen -= 1

        self._update_experiment_info()
        self._update_individuals_figure()

    def on_next_gen_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [NEXT_GEN_BUTTON] - Executing on_next_gen_button_clicked function'.format(self._experiment_name))
        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        number_of_gens = experiment_info["generations"]

        if self._current_gen < number_of_gens:
            self._current_gen += 1

        self._update_experiment_info()
        self._update_individuals_figure()

    def on_test_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [TEST_BUTTON] - Executing on_test_button_clicked function'
                     .format(self._experiment_name))

        test_indiv_edit = self._autogenerated_object.test_indiv_edit
        if test_indiv_edit.text() == "":
            logger.warn('[EXPERIMENT {0}] [TEST_BUTTON] - The individual value cannot be an empty string'
                        .format(self._experiment_name))
            QMessageBox.information(self, "Test Individual",
                                    "The individual value cannot be an empty string.", QMessageBox.Ok)
            return

        # Calculate individual cost
        try:
            individual = Individual()
            individual.generate(test_indiv_edit.text())
            callback = EvaluatorFactory.get_callback()
            cost = callback.cost(individual)
            test_label_result = self._autogenerated_object.test_label_result
            test_label_result.setText(str(cost))
        except:
            logger.error('[EXPERIMENT {0}] [TEST_BUTTON] - Error while evaluation individual. '
                         'Check the expression to be correct.'.format(self._experiment_name))
            QMessageBox.critical(self, "Test Individual",
                                 "Error while evaluation individual. Check the expression to be correct",
                                 QMessageBox.Ok)

    def on_log_check_clicked(self):
        logger.debug('[EXPERIMENT {0}] [LOG_CHECK_CLICKED] - Executing on_log_check_clicked function'
                     .format(self._experiment_name))
        self._update_individuals_figure()

    def on_show_all_check_clicked(self):
        logger.debug('[EXPERIMENT {0}] [SHOW_ALL_CHECK_CLICKED] - Executing on_show_all_check_clicked function'
                     .format(self._experiment_name))
        self._update_individuals_figure()

    def on_dimension_check_clicked(self):
        logger.debug('[EXPERIMENT {0}] [DIMENSION_CHECK_CLICKED] - Executing on_dimension_check_clicked function'
                     .format(self._experiment_name))
        # TODO: Don't know what the 3D graphic option should do yet...

    def on_save_config_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [SAVE_CONFIG_BUTTON_CLICKED] - Executing on_save_config_button_clicked function'
                     .format(self._experiment_name))
        self._persist_experiment_config()

    def on_tab_changed(self, tab_index):
        logger.debug('[EXPERIMENT {0}] [TAB_CHANGED] - Executing on_tab_changed function'
                     .format(self._experiment_name))
        self._ask_if_experiment_config_must_be_saved()

    def on_import_config_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [IMPORT_CONFIG_BUTTON_CLICKED] - Executing on_import_config_button_clicked function'
                     .format(self._experiment_name))

    def on_export_config_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [EXPORT_CONFIG_BUTTON_CLICKED] - Executing on_export_config_button_clicked function'
                     .format(self._experiment_name))

    def on_ev_edit_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [EV_EDIT_BUTTON_CLICKED] - Executing on_ev_edit_button_clicked function'
                     .format(self._experiment_name))

    def on_preev_edit_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [PREEV_EDIT_BUTTON_CLICKED] - Executing on_preev_edit_button_clicked function'
                     .format(self._experiment_name))

    def _config_table_edited(self, left, right):
        config_table = self._autogenerated_object.config_table
        table_model = config_table.model()

        # Get section, parameter and value of the parameter modified
        parameter = table_model.get_data(left.row(), 0)
        section = table_model.get_data(left.row(), 1)
        value = table_model.get_data(left.row(), 2)

        # Modify the experiment config in memory, not the one in the project
        self._experiment_config[section][parameter] = value
        logger.debug('[EXPERIMENT {0}] [CONFIG TABLE] - Parameter ({1}, {2}) edited. New Value: {3}'
                     .format(self._experiment_name, section, parameter, value))
        self._autogenerated_object.save_config_button.setDisabled(False)

    def _db_view_edited(self, left, right):
        # TODO
        pass

    def _update_individuals_per_generation_list(self):
        # Clean up ye olde list
        self._individuals_per_generation = []

        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        number_of_gens = experiment_info["generations"]
        indivs_per_gen = experiment_info["individuals_per_generation"]

        if number_of_gens == 0:
            # Disable Experiment tab buttons
            self._autogenerated_object.graph_frame.setDisabled(True)
            self._autogenerated_object.results_buttons_frame.setDisabled(True)
            return
        else:
            self._autogenerated_object.graph_frame.setDisabled(False)
            self._autogenerated_object.results_buttons_frame.setDisabled(False)

        # Complete the list
        individuals = self._mlc_local.get_individuals(self._experiment_name)
        for index in xrange(1, number_of_gens + 1):
            gens_list = []

            generation = self._mlc_local.get_generation(self._experiment_name, index)
            pop_individuals = generation.get_individuals()
            costs = generation.get_costs()
            gen_methods = generation.get_gen_methods()

            for pop_index in xrange(1, indivs_per_gen + 1):
                indiv_index = pop_individuals[pop_index - 1] - 1
                indiv_cost = costs[pop_index - 1]
                indiv_value = individuals[indiv_index].get_value()
                indiv_appearences = individuals[indiv_index].get_appearences()
                indiv_gen_method = Population.gen_method_description(gen_methods[pop_index - 1])
                gens_list.append([pop_index, indiv_index + 1, indiv_gen_method,
                                  indiv_appearences, indiv_cost, indiv_value])

            self._individuals_per_generation.append(gens_list)

    def _load_experiment_config(self):
        header = ['Parameter', 'Section', 'Value']
        editable_columns = [2]

        self._experiment_config = self._mlc_local.get_experiment_configuration(self._experiment_name)
        table_model = ConfigDictTableModel("CONFIG TABLE", self._experiment_config, header, self)

        config_table = self._autogenerated_object.config_table
        config_table.setModel(table_model)
        config_table.resizeColumnsToContents()
        config_table.setSortingEnabled(True)
        config_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        table_model.set_editable_columns(editable_columns)
        table_model.set_data_changed_callback(self._config_table_edited)
        table_model.sort_by_col(1)

    def _update_experiment_info(self):
        # Fill the comboboxes
        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        from_gen_combo = self._autogenerated_object.from_gen_combo
        to_gen_combo = self._autogenerated_object.to_gen_combo
        from_gen_combo.clear()
        to_gen_combo.clear()

        number_of_gens = experiment_info["generations"]
        if number_of_gens == 0:
            from_gen_combo.addItems([str(1)])
            to_gen_combo.addItems([str(x) for x in xrange(2, ExperimentDialog.MAX_GENERATIONS)])
        else:
            # FIXME: Think what to do in the border case of number_of_gens == MAX_GENERATIONS
            from_gen_combo.addItems([str(x) for x in xrange(1, number_of_gens + 1)])
            to_gen_combo.addItems([str(x) for x in xrange(number_of_gens + 1, ExperimentDialog.MAX_GENERATIONS)])

        # Fill the db_view
        gen_count_label = self._autogenerated_object.gen_count_label
        if number_of_gens != 0:
            if self._current_gen == 0:
                self._current_gen = 1

            header = ['Population Index', 'Individual Index', 'Gen Method', 'Appearences', 'Cost', 'Value']
            editable_columns = [4, 5]
            table_model = ConfigTableModel("DB TABLE", self._individuals_per_generation[self._current_gen - 1],
                                           header, self)
            db_view = self._autogenerated_object.db_view
            db_view.setModel(table_model)
            db_view.resizeColumnsToContents()
            db_view.setSortingEnabled(True)
            table_model.set_editable_columns(editable_columns)
            table_model.sort_by_col(0)

            # Refresh the gen_count_label
            gen_count_label.setText("<b> Generation: {0}/{1}</b>".format(self._current_gen, number_of_gens))
        else:
            self._current_gen = 0
            gen_count_label.setText("")

    def _update_individuals_figure(self):
        if self._current_gen != 0:
            # Insert the widget into the widget
            indiv_graph_frame = self._autogenerated_object.indiv_graph_frame
            # FIXME: The layouts names are autogenerated. I don't have control over them.
            # Find out if there is a way to set them with proper names
            horizontalLayout_2 = self._autogenerated_object.horizontalLayout_2

            # Matplotlib graphs
            # indiv_canvas = CostPerIndividualCanvas(indiv_graph_frame, width=5, height=4, dpi=85)
            # indiv_canvas.set_costs(current_generation.get_costs())
            # indiv_canvas.set_xlabel('Individuals')
            # indiv_canvas.set_ylabel('Costs')
            # indiv_canvas.set_title('Cost Per Individual')
            # indiv_canvas.compute_initial_figure(self._autogenerated_object.log_check.isChecked())

            # Draw current generation
            current_generation = self._mlc_local.get_generation(self._experiment_name, self._current_gen)
            costs = current_generation.get_costs()
            samples = np.linspace(1, len(costs), len(costs), dtype=int)
            indiv_chart = QtChartWrapper()
            indiv_chart.set_title('Cost Per Individual')
            ylog = self._autogenerated_object.log_check.isChecked()
            indiv_chart.set_xaxis(log=False, label="Individuals",
                                  label_format='%i', tick_count=10)
            indiv_chart.set_yaxis(log=ylog, label="Costs",
                                  label_format='%g', tick_count=10)
            indiv_chart.add_data(samples, costs, color=Qt.red, line_width=2)

            # Draw all generations only if the show_all button is selected
            if self._autogenerated_object.show_all_check.isChecked():
                experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
                number_of_gens = experiment_info["generations"]

                for index in xrange(1, number_of_gens + 1):
                    if index == self._current_gen:
                        continue
                    gen = self._mlc_local.get_generation(self._experiment_name, index)
                    costs = gen.get_costs()
                    indiv_chart.add_data(samples, costs, color=Qt.blue, line_width=1)

            indiv_canvas = indiv_chart.get_widget()

            # Remove all previous widgets before rendering again
            for i in reversed(range(horizontalLayout_2.count())):
                horizontalLayout_2.itemAt(i).widget().setParent(None)
            # Add the Indiv Canvas
            horizontalLayout_2.addWidget(indiv_canvas)

    def _persist_experiment_config(self):
        try:
            self._mlc_local.set_experiment_configuration(self._experiment_name, self._experiment_config)
        except:
            exc_type, value, traceback = sys.exc_info()
            logger.error('[EXPERIMENT {0}] [PERSIST_CONFIG] - Error while persisting experiment config file. '
                         'Type: {0} - Value: {1} - Traceback: {2}'
                         .format(self._experiment_name, exc_type, value, traceback))
            return
        self._autogenerated_object.save_config_button.setDisabled(True)

    def _ask_if_experiment_config_must_be_saved(self):
        """
        First, ask if the experiment need to be saved. If not, retrieve the
        previous configuration
        """
        if self._autogenerated_object.save_config_button.isEnabled():
            response = QMessageBox.question(self, "Save Experiment Config",
                                            "Experiment config has changed. Do you want to persist the changes made?",
                                            QMessageBox.Yes | QMessageBox.No,
                                            QMessageBox.Yes)
            if response == QMessageBox.Yes:
                self._persist_experiment_config()
            else:
                self._load_experiment_config()

            self._autogenerated_object.save_config_button.setDisabled(True)
