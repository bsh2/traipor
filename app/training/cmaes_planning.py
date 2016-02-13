import cma
from scipy.optimize import differential_evolution as scipy_de
from scipy.optimize import minimize
import numpy as np

WORKLOAD_FACTOR = 0.001


def objective_f(loads, *args):
    '''objective function to be minimized'''
    goal = args[0]
    model_perf_func = args[1]
    model_parameters = args[2]
    training_days = args[3]
    plan_length = args[4]
    prequel_plan = args[5]
    pp_func = args[6]
    plan = map_loads_to_training_days(loads, training_days, plan_length)
    plan = pp_func(plan)
    plan_perf = model_perf_func(prequel_plan + plan, **model_parameters)
    total_workload = sum(plan)
    fitness_wo_load = abs(goal - plan_perf)
    fitness_with_load = fitness_wo_load + WORKLOAD_FACTOR * total_workload
    return fitness_with_load


def map_loads_to_training_days(loads, training_days, plan_length):
    plan = [0.0] * plan_length
    for i, l in zip(training_days, loads):
        plan[i] = l
    return plan


def genplan(length,  # in weeks
            goal,
            training_days,
            max_load,
            model_func,
            prequel_plan,
            pp_func,
            **model_parameters):
    '''generate a plan with cma.fmin'''
    x0 = [0.0] * len(training_days)
    options = cma.CMAOptions()
    options.set('bounds', [0.0, max_load])
    # options.set('verb_disp', 0)
    # options.set('verbose', -9)
    # options.set('verb_log', 0)
    # options.set('maxiter', 800)
    args = (goal, model_func, model_parameters, training_days, length * 7,
            prequel_plan, pp_func)
    print('max_load {}'.format(max_load))
    sigma = max_load / 4
    solution = cma.fmin(objective_f, x0, sigma, args=args, options=options)
    plan = map_loads_to_training_days(solution[0], training_days, length * 7)
    return plan


def genplan_de(length,  # in weeks
               goal,
               training_days,
               max_load,
               model_func,
               prequel_plan,
               pp_func,
               **model_parameters):
    bounds = [(0, max_load)] * len(training_days)
    args = (goal, model_func, model_parameters, training_days, length * 7,
            prequel_plan, pp_func)
    solution = scipy_de(objective_f,
                        bounds, args=args,
                        mutation=(1, 1.99),
                        recombination=0.5,
                        disp=True)
    solution.x = pp_func(solution.x)
    plan = map_loads_to_training_days(solution.x, training_days, length * 7)
    return plan


def genplan_minimize(length,  # in weeks
                     goal,
                     training_days,
                     max_load,
                     model_func,
                     prequel_plan,
                     pp_func,
                     **model_parameters):
    x0 = np.array([0.0] * len(training_days))  # initial guess
    args = (goal, model_func, model_parameters, training_days, length * 7,
            prequel_plan, pp_func)
    bounds = [(0.0, max_load)] * len(training_days)
    options = {'maxiter': 400, 'disp': False}

    def iter_callback(xk):
        print("current parameter vector: {}".format(xk))

    optres = minimize(objective_f,
                      x0,
                      args,
                      'L-BFGS-B',
                      bounds=bounds,
                      options=options,
                      callback=iter_callback)
    return optres
