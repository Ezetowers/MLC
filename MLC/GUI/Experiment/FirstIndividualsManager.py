from MLC.GUI.Tables.ConfigTableModel import ConfigTableModel
from MLC.GUI.util import test_individual_value
from MLC.Log.log import get_gui_logger
from MLC.individual.Individual import Individual
from MLC.mlc_parameters.mlc_parameters import Config
from MLC.Population.Creation.IndividualSelection import IndividualSelection
from MLC.Population.Creation.CreationFactory import CreationFactory
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox

logger = get_gui_logger()


class FirstIndividualsManager(object):

    def __init__(self, parent, experiment_name, autogenerated_object, mlc_local):
        self._parent = parent
        self._individuals = []
        self._experiment_name = experiment_name
        self._autogenerated_object = autogenerated_object
        self._first_indivs_table = self._autogenerated_object.first_indivs_table
        self._mlc_local = mlc_local

    def add_individual(self):
        indiv = QInputDialog.getText(self._parent, "Add Individual",
                                     "Insert the value of the individual to be added.")

        if indiv[1] == True:
            # Check if the individual inserted is empty
            if not indiv[0]:
                logger.info("[FIRST_INDIVS_MANAGER] Experiment {0} - "
                            "Indiv inserted was empty. Indiv won't be inserted."
                            .format(self._experiment_name))
                QMessageBox.warning(self._parent,
                                    "Individual inserted is empty. ",
                                    "Please, insert a non empty individual")
                return

            indiv_value = indiv[0]
            if test_individual_value(parent=self._parent,
                                     experiment_name=self._experiment_name,
                                     log_prefix="[FIRST_INDIVS_MANAGER]",
                                     indiv_value=indiv_value,
                                     config=Config.get_instance()):
                self._individuals.append(indiv_value)
                self._load_table()

                QMessageBox.information(self._parent, "Individual added",
                                        "Individual {0} was succesfully added"
                                        .format(indiv_value))
                logger.info("[FIRST_INDIVS_MANAGER] Experiment {0} - "
                            "Individual {1} was succesfully added"
                            .format(self._experiment_name, indiv_value))

    def add_individuals_from_textfile(self):
        pass

    def modify_individual(self, indiv_index):
        pass

    def remove_individual(self, indiv_index):
        pass

    def get_gen_creator(self):
        """
        Return an IndividualSelection creator if the user added individuals
        manually.
        Return None if this was not the case
        """
        if not self._individuals:
            logger.info("[FIRST_INDIV] No individual")
            return None

        gen_method = Config.get_instance().get('GP', 'generation_method')
        fill_creator = CreationFactory.make(gen_method)

        # Creat the dictionary of individuals
        indivs_dict = {}
        for index in xrange(len(self._individuals)):
            indiv = Individual(self._individuals[index])
            indivs_dict[indiv] = [index]

        return IndividualSelection(indivs_dict, fill_creator)

    def _load_table(self):
        header = ['Index', 'Value']

        # Generate the dict to be used by the Table Model
        indivs_list = []
        for index in xrange(len(self._individuals)):
            indivs_list.append([index + 1, self._individuals[index]])

        table_model = ConfigTableModel(name="FIRST INDIVS TABLE",
                                       data=indivs_list,
                                       header=header,
                                       parent=self._parent)

        self._first_indivs_table.setModel(table_model)
        self._first_indivs_table.setDisabled(False)
        self._first_indivs_table.setVisible(False)
        self._first_indivs_table.resizeColumnsToContents()
        self._first_indivs_table.setVisible(True)
        self._first_indivs_table.setSortingEnabled(True)

    def _test_individual_value(self, indiv_value):
        """
        Evaluate an individual in order to check its correctness. If the evaluation
        throw any exception, it won't be handled in this method
        """
        LispTreeExpr.check_expression(indiv_value)
        individual = Individual.generate(config=Config.get_instance(),
                                         rhs_value=indiv_value)
        callback = EvaluatorFactory.get_callback()
        return callback.cost(individual)
