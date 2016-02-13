from scipy import optimize
import lmfit
import numpy as np
import cma

try:
    from .fitnessfatigue import performance_over_time as \
        ff_performance_over_time
    from .fitnessfatigue import performance_over_time2 as \
        ff_performance_over_time2
    from .perpot import performance_over_time as pp_performance_over_time
    from .perpot import performance_over_time2 as pp_performance_over_time2
    from .perpot import calc_pp_load_scale_factor, calc_pp_perf_scale_factor
    from .fitting_util import filter_model_perf_values_2_load_days
    from .fitting_util import filter_model_perfs_2_real_perfs
    from .fitting_util import csv_value_dict_from_path
    from .fitting_util import plan_perfs_from_dic, calc_rmse, calc_residuals
except SystemError:
    from fitnessfatigue import performance_over_time as ff_performance_over_time
    from fitnessfatigue import performance_over_time2 as \
        ff_performance_over_time2
    from perpot import performance_over_time as pp_performance_over_time
    from perpot import performance_over_time2 as pp_performance_over_time2
    from perpot import calc_pp_load_scale_factor, calc_pp_perf_scale_factor
    # from fitting_util import choose_initial_p
    from fitting_util import filter_model_perf_values_2_load_days
    from fitting_util import filter_model_perfs_2_real_perfs
    # from plots import plot_model_and_metrics
    # from plots import plot_model_and_metrics2
    # from plots import pp_plot_model_and_metrics2
    from fitting_util import csv_value_dict_from_path
    from fitting_util import plan_perfs_from_dic, calc_rmse, calc_residuals


def objective_f(x, *args):
    '''the objective function to minimize with the optimization methods. returns
    the calculated error'''
    plan = args[0]
    real_perfs = args[1]
    calc_error = args[2]
    unpack_parms = args[3]
    model_func = args[4]
    model_parms = unpack_parms(x)
    model_perfs = model_func(plan, model_parms)
    model_perfs = filter_model_perfs_2_real_perfs(model_perfs, real_perfs)
    real_perfs = list(filter(lambda x: x > 0.0, real_perfs))
    assert(len(model_perfs) == len(real_perfs))
    return calc_error(np.array(real_perfs), np.array(model_perfs))


def unpack_ff_parms_list(x):
    return x


def unpack_pp_parms_list(x):
    # optimize delays and init_p aka perfpot
    return [0.0, 0.0, x[0], x[1], x[2], x[3]]


def unpack_ff_lmfit_parms(x):
    parvals = x.valuesdict()
    return [parvals['initial_p'], parvals['k_1'], parvals['tau_1'],
            parvals['k_2'], parvals['tau_2']]


def unpack_pp_lmfit_parms(x):
    # optimize delays and init_p aka perfpot
    parvals = x.valuesdict()
    return [0.0, 0.0, parvals['perfpot'], parvals['straindelay'],
            parvals['responsedelay'], parvals['overflowdelay']]


def ff_minimize_fitting(plan, real_perf_values, method):
    '''generic interface for optimization.minimize for Fitness Fatigue fitting.
    returns the OptimizeResult object.'''
    x0 = np.array([real_perf_values[0], 1.0, 30.0, 1.0, 15.0])  # initial guess
    args = (plan,
            real_perf_values,
            calc_rmse,
            unpack_ff_parms_list,
            ff_performance_over_time2)
    bounds = [(0, max(real_perf_values)),  # initial_p
              (0.01, 5),                   # k_1
              (1, 70),                     # tau_1
              (0.01, 5),                   # k_2
              (1, 70)]                     # tau_2
    # options = {'maxiter': 50, 'disp': True}
    options = {'disp': False}

    def iter_callback(xk):
        print("current parameter vector: {}".format(xk))

    return optimize.minimize(objective_f,
                             x0,
                             args,
                             method,
                             bounds=bounds,
                             options=options,
                             callback=None)
                             # callback=iter_callback)


def pp_minimize_fitting(plan, real_perf_values, method):
    '''generic interface for optimization.minimize for PerPot fitting.
    returns the OptimizeResult object and the scale factors.'''
    # x0 = np.array([4.0, 2.0, 0.001])  # initial guess
    x0 = np.array([0.5, 4.0, 2.0, 15])  # initial guess including perfpot
    load_scale_factor = calc_pp_load_scale_factor(plan)
    perf_scale_factor = calc_pp_perf_scale_factor(real_perf_values)
    scaled_plan = list(map(lambda l: load_scale_factor * l, plan))
    scaled_perfs = list(map(lambda p: perf_scale_factor * p, real_perf_values))
    args = (scaled_plan,
            scaled_perfs,
            calc_rmse,
            unpack_pp_parms_list,
            pp_performance_over_time2)
    bounds = [(0.0, 1.0),       # perfpot
              (0.001, 30.0),    # DS Delay of Strain Rate
              (0.001, 30.0),    # DR Delay of Response Rate
              (0.001, 30.0)]    # DSO Delay of Strain Overflow Rate
    options = {}
    # options['maxiter'] = 50
    options['disp'] = False

    def iter_callback(xk):
        print("current parameter vector: {}".format(xk))

    optres = optimize.minimize(objective_f,
                               x0,
                               args,
                               method,
                               bounds=bounds,
                               options=options,
                               callback=iter_callback)
    return optres, load_scale_factor, perf_scale_factor


def ff_cmaes_fitting(plan, real_perf_values):
    x0 = np.array([real_perf_values[0], 1.0, 30.0, 1.0, 15.0])  # initial guess
    args = (plan,
            real_perf_values,
            calc_rmse,
            unpack_ff_parms_list,
            ff_performance_over_time2)
    opts = cma.CMAOptions()
    bounds = [[0.0, 0.01, 1.0, 0.01, 1.0],
              [real_perf_values[0] * 2, 5.0, 70.0, 5.0, 70.0]]
    opts.set('bounds', bounds)
    opts.set('tolfun', 1e-5)
    # opts.set('verb_disp', False)
    # opts.set('verbose', -9)
    # opts.set('maxiter', 800)
    res = cma.fmin(objective_f, x0, 0.5, args=args, options=opts)
    return res


def pp_cmaes_fitting(plan, real_perf_values):
    # x0 = np.array([4.0, 2.0, 15])  # initial guess of delays
    x0 = np.array([0.5, 4.0, 2.0, 15])  # initial guess including perfpot
    load_scale_factor = calc_pp_load_scale_factor(plan)
    perf_scale_factor = calc_pp_perf_scale_factor(real_perf_values)
    scaled_plan = list(map(lambda l: load_scale_factor * l, plan))
    scaled_perfs = list(map(lambda p: perf_scale_factor * p, real_perf_values))
    args = (scaled_plan,
            scaled_perfs,
            calc_rmse,
            unpack_pp_parms_list,
            pp_performance_over_time2)
    opts = cma.CMAOptions()
    # only optimize delays
    '''bounds = [[0.001, 0.001, 0.001],
              [30.0, 30.0, 30.0]]'''
    # optimize delays and init_p aka perfpot
    bounds = [[0.0, 0.001, 0.001, 0.001],
              [1.0, 30.0, 30.0, 30.0]]
    opts.set('bounds', bounds)
    # opts.set('verb_disp', False)
    # opts.set('verbose', -9)
    opts.set('maxiter', 800)
    res = cma.fmin(objective_f, x0, 0.5, args=args, options=opts)
    print('res[0] = {}'.format(res[0]))
    print('res[1] = {}'.format(res[1]))
    return res, load_scale_factor, perf_scale_factor


def ff_lmfit_fitting(plan, real_perf_values, method='leastsq'):
    '''least squares or differential evolution fitting with bounds'''
    real_perf_values = np.array(real_perf_values)
    args = (plan,
            real_perf_values,
            calc_residuals,
            unpack_ff_lmfit_parms,
            ff_performance_over_time2)
    params = lmfit.Parameters()
    params.add(name='initial_p',
               value=real_perf_values[0],
               min=0,
               max=max(real_perf_values))
    params.add(name='k_1', value=1.0, min=0.01, max=5.0)
    params.add(name='tau_1', value=30.0, min=1.00, max=70.0)
    params.add(name='k_2', value=1.0, min=0.01, max=5.0)
    params.add(name='tau_2', value=15.0, min=1.00, max=70.0)
    lmfit.minimize(objective_f, params, method=method, args=args)
    model_perfs = ff_performance_over_time(plan,
                                           params['initial_p'],
                                           params['k_1'],
                                           params['tau_1'],
                                           params['k_2'],
                                           params['tau_2'])
    model_perfs = filter_model_perfs_2_real_perfs(model_perfs, real_perf_values)
    real_perf_values = list(filter(lambda x: x > 0.0, real_perf_values))
    assert(len(model_perfs) == len(real_perf_values))
    rmse = calc_rmse(real_perf_values, model_perfs)
    return (params['initial_p'].value,
            params['k_1'].value,
            params['tau_1'].value,
            params['k_2'].value,
            params['tau_2'].value), rmse


def pp_lmfit_fitting(plan, real_perf_values, method='leastsq'):
    '''least squares or differential evolution fitting with bounds'''
    real_perf_values = np.array(real_perf_values)
    load_scale_factor = calc_pp_load_scale_factor(plan)
    perf_scale_factor = calc_pp_perf_scale_factor(real_perf_values)
    scaled_plan = list(map(lambda l: load_scale_factor * l, plan))
    scaled_perfs = list(map(lambda p: perf_scale_factor * p, real_perf_values))
    args = (scaled_plan,
            np.array(scaled_perfs),
            calc_residuals,
            unpack_pp_lmfit_parms,
            pp_performance_over_time2)
    params = lmfit.Parameters()
    params.add(name='perfpot', value=0.5, min=0, max=1)
    params.add(name='straindelay', value=4.0, min=0.001, max=30)
    params.add(name='responsedelay', value=2.0, min=0.001, max=30)
    params.add(name='overflowdelay', value=15, min=0.001, max=30)
    lmfit.minimize(objective_f, params, method=method, args=args)
    model_perfs = pp_performance_over_time(scaled_plan,
                                           0.0,
                                           0.0,
                                           params['perfpot'],
                                           params['straindelay'],
                                           params['responsedelay'],
                                           params['overflowdelay'])
    model_perfs = filter_model_perfs_2_real_perfs(model_perfs, real_perf_values)
    scaled_perfs = list(filter(lambda x: x > 0.0, scaled_perfs))
    assert(len(model_perfs) == len(scaled_perfs))
    rmse = calc_rmse(scaled_perfs, model_perfs)
    return (((params['perfpot'].value,
            params['straindelay'].value,
            params['responsedelay'].value,
            params['overflowdelay'].value), rmse),
            load_scale_factor,
            perf_scale_factor)
