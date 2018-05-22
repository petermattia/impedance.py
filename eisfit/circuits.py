from .fitting import circuit_fit, computeCircuit, calculateCircuitLength
import numpy as np


class BaseCircuit:
    """ A base class for all circuits

    """
    def __init__(self, initial_guess=None, algorithm='leastsq', bounds=None):
        """
        Constructor for the Randles' circuit class


        """
        if initial_guess is not None:
            for i in initial_guess:
                assert isinstance(i, (float, int, np.int32, np.float64)), \
                       'value {} in initial_guess is not a number'.format(i)
        self.initial_guess = initial_guess
        self.parameters_ = None
        self.bounds = bounds

    def fit(self, frequencies, impedance):
        """
        Fit the circuit model

        Parameters
        ----------
        frequencies: numpy array
            Frequencies

        impedance: numpy array of dtype 'complex128'
            Impedance values to fit

        Returns
        -------
        self: returns an instance of self

        """
        # tests
        import numpy as np
        assert isinstance(frequencies, np.ndarray)
        assert len(frequencies) == len(impedance)
        assert isinstance(frequencies[0], (float, int, np.int32, np.float64)),\
            'frequencies does not contain a number'
        # check_valid_impedance()
        if self.initial_guess is not None:
            self.parameters_, _ = circuit_fit(frequencies, impedance,
                                              self.circuit, self.initial_guess,
                                              self.algorithm,
                                              bounds=self.bounds)
        else:
            # TODO auto calc guess
            raise ValueError('no initial guess supplied')

        return self

    def _is_fit(self):
        if self.parameters_ is not None:
            return True
        else:
            return False

    def predict(self, frequencies):
        """ Predict impedance using a fit model

        Parameters
        ----------
        frequencies: numpy array
            Frequencies

        Returns
        -------
        impedance: numpy array of dtype 'complex128'
            Predicted impedance

        """

        if self._is_fit():
            # print('Output! {}'.format(self.parameters_))

            return computeCircuit(self.circuit,
                                  self.parameters_.tolist(),
                                  frequencies.tolist())

        else:
            raise ValueError("The model hasn't been fit yet")

    def __repr__(self):
        """
        Defines the pretty printing of the circuit

        """
        if self._is_fit():
            return "{} circuit (fit values={}, \
                    circuit={})".format(self.name,
                                        self.parameters_,
                                        self.circuit)
        else:
            return "{} circuit (initial_guess={}, \
                    circuit={})".format(self.name,
                                        self.initial_guess,
                                        self.circuit)


class Randles(BaseCircuit):
    def __init__(self, initial_guess=None, CPE=False,
                 algorithm='leastsq', bounds=None):
        """ Constructor for the Randles' circuit class

        Parameters
        ----------
        initial_guess: list of floats
            A list of values to use as the initial guess
        CPE: boolean
            Use a constant phase element instead of a capacitor
        """
        self.name = 'Randles'
        self.parameters_ = None
        self.initial_guess = initial_guess
        self.algorithm = algorithm
        self.bounds = bounds
        # write some asserts to enforce typing
        if initial_guess is not None:
            for i in initial_guess:
                assert isinstance(i, (float, int, np.int32, np.float64)), \
                       'value {} in initial_guess is not a number'.format(i)

        if CPE:
            self.circuit = 'R_0-p(R_1,E_1/E_2)-W_1/W_2'
            circuit_length = calculateCircuitLength(self.circuit)
            assert len(initial_guess) == circuit_length, \
                'Initial guess length needs to be equal to {circuit_length}'
        else:
            self.circuit = 'R_0-p(R_1,C_1)-W_1/W_2'

            circuit_length = calculateCircuitLength(self.circuit)
            assert len(initial_guess) == circuit_length, \
                'Initial guess length needs to be equal to {circuit_length}'


class DefineCircuit(BaseCircuit):
    def __init__(self, initial_guess=None, circuit=None,
                 algorithm='leastsq', bounds=None):
        """
        Constructor for the Randles' circuit class

        Inputs
        ------
        initial_guess: A list of values to use as
                       the initial guess for element values
        CPE: Whether or not to use constant phase elements
             in place of a Warburg element

        Methods
        -------

        .fit(frequencies, impedances)
            frequencies: A list of frequencies where the
                         values should be tested
            impedances: A list of impedances used to fitting using
                        scipy's least_squares fitting algorithm.
        .predict(frequencies)
            frequencies: A list of frequencies where new
                         values will be calculated
        """

        self.name = 'Custom'
        self.parameters_ = None
        self.initial_guess = initial_guess
        self.circuit = circuit
        self.algorithm = algorithm
        self.bounds = bounds
        # write some asserts to enforce typing
        if initial_guess is not None:
            for i in initial_guess:
                assert isinstance(i, (float, int, np.int32, np.float64)), \
                       'value {} in initial_guess is not a number'.format(i)

            circuit_length = calculateCircuitLength(self.circuit)
            assert len(initial_guess) == circuit_length, \
                'Initial guess length needs to be equal to {circuit_length}'


class FlexiCircuit(BaseCircuit):
    def __init__(self, max_elements=None, generations=2,
                 popsize=30, initial_guess=None):
        """
        Constructor for the Flexible Circuit class

        Parameters
        ----------
        max_elements: integer
            The maximum number of elements available to the algorithm
        solve_time: integer
            The maximum allowed solve time, in seconds.

        """

        self.name = 'Flexible Circuit'
        self.initial_guess = initial_guess
        self.generations = generations
        self.popsize = popsize
        self.max_elements = max_elements
#        self.bounds = bounds

    def fit(self, frequencies, impedances):
        from scipy.optimize import leastsq
        from .genetic import make_population
        from .fitting import residuals
        n = 5
        f = frequencies
        Z = impedances
        for i in range(self.generations):
            scores = []
            self.population = make_population(self.popsize, n)
            for pop in self.population:
                self.circuit = pop
                print(self.circuit)
                circuit_length = calculateCircuitLength(self.circuit)
#                for j in range(n-4,n+4):
#                    print(residuals(self.initial_guess,Z,f,self.circuit))
#                    try:
#                        print(self.circuit)
                self.initial_guess = list(np.ones(circuit_length)/10)
#                        print(residuals(self.initial_guess,Z,F,))
#                        print(self.initial_guess)
                p_values, covar, ff, _, _ = leastsq(residuals,
                                                    self.initial_guess,
                                                    args=(Z, f, self.circuit),
                                                    maxfev=100000, ftol=1E-13,
                                                    full_output=True)

                print(p_values)
                scores.append([np.square(ff['fvec']).mean(), pop])

        print(scores)
        return scores