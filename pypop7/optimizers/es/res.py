import numpy as np

from pypop7.optimizers.es.es import ES


class RES(ES):
    """Rechenberg's (1+1)-Evolution Strategy with 1/5th success rule (RES).

    .. note:: `RES` is the first ES with self-adaptation of the global step-size, designed by Rechenberg. Since
       there is only one parent and only one offspring for each generation, `RES` generally shows very limited
       *exploration* ability for large-scale black-box optimization (LSBBO).

       It is **highly recommended** to first attempt other more advanced ES variants for LSBBO. Here we include it
       mainly for *benchmarking* and *theoretical* purpose.

    Parameters
    ----------
    problem : dict
              problem arguments with the following common settings (`keys`):
                * 'fitness_function' - objective function to be **minimized** (`func`),
                * 'ndim_problem'     - number of dimensionality (`int`),
                * 'upper_boundary'   - upper boundary of search range (`array_like`),
                * 'lower_boundary'   - lower boundary of search range (`array_like`).
    options : dict
              optimizer options with the following common settings (`keys`):
                * 'max_function_evaluations' - maximum of function evaluations (`int`, default: `np.Inf`),
                * 'max_runtime'              - maximal runtime (`float`, default: `np.Inf`),
                * 'seed_rng'                 - seed for random number generation needed to be *explicitly* set (`int`),
                * 'record_fitness'           - flag to record fitness list to output results (`bool`, default: `False`),
                * 'record_fitness_frequency' - function evaluations frequency of recording (`int`, default: `1000`),

                  * if `record_fitness` is set to `False`, it will be ignored,
                  * if `record_fitness` is set to `True` and it is set to 1, all fitness generated during optimization
                    will be saved into output results.

                * 'verbose'                  - flag to print verbose info during optimization (`bool`, default: `True`),
                * 'verbose_frequency'        - frequency of printing verbose info (`int`, default: `10`);
              and with three particular settings (`keys`):
                * 'mean'          - initial (starting) point, mean of Gaussian search distribution (`array_like`),
                * 'sigma'         - initial global step-size (σ), mutation strength (`float`),
                * 'eta_sigma'     - learning rate of global step-size (`float`, default:
                  `1.0 / np.sqrt(problem['ndim_problem'] + 1.0)`).

    Examples
    --------
    Use the ES optimizer `RES` to minimize the well-known test function
    `Rosenbrock <http://en.wikipedia.org/wiki/Rosenbrock_function>`_:

    .. code-block:: python
       :linenos:

       >>> import numpy
       >>> from pypop7.benchmarks.base_functions import rosenbrock  # function to be minimized
       >>> from pypop7.optimizers.es.res import RES
       >>> problem = {'fitness_function': rosenbrock,  # define problem arguments
       ...            'ndim_problem': 2,
       ...            'lower_boundary': -5 * numpy.ones((2,)),
       ...            'upper_boundary': 5 * numpy.ones((2,))}
       >>> options = {'max_function_evaluations': 5000,  # set optimizer options
       ...            'seed_rng': 2022,
       ...            'mean': 3 * numpy.ones((2,)),
       ...            'sigma': 0.1}
       >>> res = RES(problem, options)  # initialize the optimizer class
       >>> results = res.optimize()  # run the optimization process
       >>> # return the number of function evaluations and best-so-far fitness
       >>> print(f"(1+1)-ES: {results['n_function_evaluations']}, {results['best_so_far_y']}")
         * Generation 10: best_so_far_y 6.53220e+01, min(y) 1.01146e+03 & Evaluations 11
         * Generation 20: best_so_far_y 4.00093e-01, min(y) 4.39918e+03 & Evaluations 21
         ...
         * Generation 4910: best_so_far_y 1.27854e-03, min(y) 1.27854e-03 & Evaluations 4989
         * Generation 4920: best_so_far_y 1.27041e-03, min(y) 1.27041e-03 & Evaluations 4999
       (1+1)-ES: 5000, 0.0012704091706297754

    Attributes
    ----------
    n_individuals : `int`
                    number of offspring (λ: lambda), offspring population size.
    n_parents     : `int`
                    number of parents (μ: mu), parental population size.
    mean          : `array_like`
                    initial (starting) point, mean of Gaussian search distribution.
    sigma         : `float`
                    initial global step-size (σ), mutation strength (`float`).
    eta_sigma     : `float`
                    learning rate of global step-size.

    References
    ----------
    Hansen, N., Arnold, D.V. and Auger, A., 2015.
    Evolution strategies.
    In Springer Handbook of Computational Intelligence (pp. 871-898). Springer, Berlin, Heidelberg.
    https://link.springer.com/chapter/10.1007%2F978-3-662-43505-2_44
    (See Algorithm 44.3 for details.)

    Beyer, H.G. and Schwefel, H.P., 2002.
    Evolution strategies–A comprehensive introduction.
    Natural Computing, 1(1), pp.3-52.
    https://link.springer.com/article/10.1023/A:1015059928466

    Rechenberg, I., 1989.
    Evolution strategy: Nature’s way of optimization.
    In Optimization: Methods and Applications, Possibilities and Limitations (pp. 106-126).
    Springer, Berlin, Heidelberg.
    https://link.springer.com/chapter/10.1007/978-3-642-83814-9_6

    Rechenberg, I., 1984.
    The evolution strategy. A mathematical model of darwinian evolution.
    In Synergetics—from Microscopic to Macroscopic Order (pp. 122-132). Springer, Berlin, Heidelberg.
    https://link.springer.com/chapter/10.1007/978-3-642-69540-7_13
    """
    def __init__(self, problem, options):
        ES.__init__(self, problem, options)
        if self.eta_sigma is None:  # for Line 5 (1 / d)
            self.eta_sigma = 1.0 / np.sqrt(self.ndim_problem + 1.0)
        assert self.eta_sigma > 0, f'`self.eta_sigma` = {self.eta_sigma}, but should > 0.'

    def initialize(self, args=None, is_restart=False):
        mean = self._initialize_mean(is_restart)  # mean of Gaussian search distribution
        y = self._evaluate_fitness(mean, args)  # fitness
        best_so_far_y = np.copy(y)
        return mean, y, best_so_far_y

    def iterate(self, args=None, mean=None):
        # sample and evaluate (only one) offspring (Line 4 and 5)
        x = mean + self.sigma*self.rng_optimization.standard_normal((self.ndim_problem,))
        y = self._evaluate_fitness(x, args)
        return x, y

    def restart_initialize(self, args=None, mean=None, y=None, best_so_far_y=None, fitness=None):
        self._fitness_list.append(self.best_so_far_y)
        is_restart_1, is_restart_2 = self.sigma < self.sigma_threshold, False
        if len(self._fitness_list) >= self.stagnation:
            is_restart_2 = (self._fitness_list[-self.stagnation] - self._fitness_list[-1]) < self.fitness_diff
        is_restart = bool(is_restart_1) or bool(is_restart_2)
        if is_restart:
            self.n_restart += 1
            self.sigma = np.copy(self._sigma_bak)
            mean, y, best_so_far_y = self.initialize(args, is_restart)
            fitness.append(y)
            self._fitness_list = [best_so_far_y]
        return mean, y, best_so_far_y

    def optimize(self, fitness_function=None, args=None):  # for all generations (iterations)
        fitness = ES.optimize(self, fitness_function)
        mean, y, best_so_far_y = self.initialize(args)
        fitness.append(y)
        while True:
            x, y = self.iterate(args, mean)
            if self.record_fitness:
                fitness.append(y)
            if self._check_terminations():
                break
            self.sigma *= np.power(np.exp(float(y < best_so_far_y) - 1 / 5), self.eta_sigma)
            self._n_generations += 1
            self._print_verbose_info(y)
            if y < best_so_far_y:
                mean, best_so_far_y = x, y
            if self.is_restart:
                mean, y, best_so_far_y = self.restart_initialize(args, mean, y, best_so_far_y, fitness)
        return self._collect_results(fitness, mean)
