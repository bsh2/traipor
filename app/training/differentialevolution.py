import numpy as np
import time

try:
    from . import fitnessfatigue as ff_model
    from . import perpot as pp_model
    from . import plan_util as u
except SystemError:
    import fitnessfatigue as ff_model
    import perpot as pp_model
    import plan_util as u

POP_SIZE = 50
GOOD_ENOUGH_THRES = 0.5


def de_operator(a, b, c, d, max_load, min_load, recomb_weight, scale_factor):
    a_p = a.copy()
    index = np.random.randint(0, len(a_p))
    for i in range(len(a_p)):
        if np.random.random() <= recomb_weight or i == index:
            a_p[i] = b[i] + scale_factor * (c[i] - d[i])
        if a_p[i] < 0.0 or 0.0 < a_p[i] < min_load:     # don't change off-days
            a_p[i] = min_load
        elif a_p[i] > max_load:
            a_p[i] = max_load
    return a_p


def generate_individual(weeks, off_days, max_load, min_load, pop_init_divisor):
    """returns a random plan with an upper bound of max_load / pop_init_divisor
    and a lower bound of min_load"""
    plan = np.random.random(weeks * 7) * (max_load / pop_init_divisor)
    for i, v in enumerate(plan):
        if v < min_load:
            plan[i] = min_load
    for i in off_days:
        plan[i] = 0.0
    return plan


def generate_population(weeks,
                        training_days,
                        pop_size,
                        max_load,
                        min_load,
                        pop_init_divisor):
    p = [np.empty(weeks * 7)] * pop_size
    off_days = u.calc_offdays(training_days, weeks)
    for i in range(pop_size):
        p[i] = generate_individual(weeks,
                                   off_days,
                                   max_load,
                                   min_load,
                                   pop_init_divisor)
    return p


def rand_scale_fac():
    f = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8,
         1.9, 2.0]
    i = np.random.randint(len(f))
    return f[i]


def differential_evolution(weeks,
                           goal,
                           training_days,
                           pop_size,
                           max_load,
                           min_load,
                           model_perf_func,
                           prequel_plan=[],     # prepend to solution candidates
                           pp_func=None,        # post processing function
                           recomb_weight=0.7,
                           scale_factor=None,   # None means dithering
                           pop_init_divisor=10,
                           **model_parameters):
    t = 0   # generation counter
    fitness_t = [0.0] * pop_size
    fitness_t_minus_1 = [0.0] * pop_size
    local_optima_counter = 0
    pops = [generate_population(weeks,
                                training_days,
                                pop_size,
                                max_load,
                                min_load,
                                pop_init_divisor)]
    if pp_func is not None:
        pops[0] = list(map(pp_func, pops[0]))
    good_enough = False
    run_time = 0
    start_time = int(time.time())
    preq_plan = np.array(prequel_plan)

    print('pop_init_divisor = {}'.format(pop_init_divisor))
    while t < 1000 and not good_enough and local_optima_counter < 40:
        pops.append([0] * pop_size)           # preallocate space for pointers
        fitness_t_minus_1 = fitness_t.copy()  # copy last run fitness values

        for i in range(pop_size):
            if scale_factor is None:
                scale_fac = rand_scale_fac()
            else:
                scale_fac = scale_factor
            a_i, b_i, c_i, d_i = np.random.choice(pop_size, 4, False)
            a, b, c, d = pops[t][a_i], pops[t][b_i], pops[t][c_i], pops[t][d_i]
            a_p = de_operator(a, b, c, d, max_load, min_load, recomb_weight, scale_fac)
            if pp_func is not None:
                a_p = pp_func(a_p)
            a_p_fit, a_p_good_enough = u.fitness(np.concatenate((preq_plan, a_p)),
                                                 goal,
                                                 GOOD_ENOUGH_THRES,
                                                 model_perf_func,
                                                 **model_parameters)
            a_fit, a_good_enough = u.fitness(np.concatenate((preq_plan, a)),
                                             goal,
                                             GOOD_ENOUGH_THRES,
                                             model_perf_func,
                                             **model_parameters)
            if a_p_fit >= a_fit:
                pops[t+1][i] = a_p
                fitness_t[i] = a_p_fit
                if a_p_good_enough:
                    good_enough = True
                    pops[t+1] = pops[t+1][:i+1]  # remove superfluous entries
                    fitness_t = fitness_t[:i+1]  # remove superfluous entries
                    break
            else:
                pops[t+1][i] = a
                fitness_t[i] = a_fit
                if a_good_enough:
                    good_enough = True
                    pops[t+1] = pops[t+1][:i+1]  # remove superfluous entries
                    fitness_t = fitness_t[:i+1]  # remove superfluous entries
                    break
        print('gen {}: max fitness {}'.format(t, max(fitness_t)))
        t += 1
        if max(fitness_t) == max(fitness_t_minus_1):
            local_optima_counter += 1
        else:
            local_optima_counter = 0
        run_time = int(time.time()) - start_time

    s = sorted(pops[-1], key=lambda p: u.fitness(np.concatenate((preq_plan, p)),
                                                 goal,
                                                 GOOD_ENOUGH_THRES,
                                                 model_perf_func,
                                                 **model_parameters)[0])
    print('run_time: {}'.format(run_time))
    print('local_optima_counter: {}'.format(local_optima_counter))
    print('good_enough: {}'.format(good_enough))
    return s[-1]


def fitnessfatigue_example(ff_args):
    weeks = 12
    goal = 1.1 * ff_args['initial_p']
    max_load = 150.0
    min_load = 0.0
    cycle_days = [u.WeekDays.monday, u.WeekDays.tuesday, u.WeekDays.wednesday,
                  u.WeekDays.friday, u.WeekDays.saturday]
    training_days = u.microcycle_days(cycle_days, weeks)
    # training_days = u.filter_weeks(training_days, [3, 7, 11])
    # print(ff_args)
    solution = differential_evolution(weeks,
                                      goal,
                                      training_days,
                                      POP_SIZE,
                                      max_load,
                                      min_load,
                                      ff_model.after_plan,
                                      prequel_plan=[],
                                      pp_func=u.sort_loads,
                                      recomb_weight=0.7,
                                      scale_factor=0.8,
                                      pop_init_divisor=1,
                                      **ff_args)
    solution_fitness = u.fitness(solution,
                                 goal,
                                 GOOD_ENOUGH_THRES,
                                 ff_model.after_plan,
                                 **ff_args)
    perf_after_plan = ff_model.after_plan(solution, **ff_args)
    u.print_ea_result(solution, solution_fitness, perf_after_plan, goal)


def perpot_example(pp_args):
    weeks = 12
    goal = 0.3
    max_load = 1.0
    cycle_days = [u.WeekDays.monday, u.WeekDays.tuesday, u.WeekDays.wednesday,
                  u.WeekDays.friday, u.WeekDays.saturday]
    training_days = u.microcycle_days(cycle_days, weeks)
    training_days = u.filter_weeks(training_days, [3, 7, 11])
    # pp_args = params.pp_parms8
    print(pp_args)
    solution = differential_evolution(weeks,
                                      goal,
                                      training_days,
                                      POP_SIZE,
                                      max_load,
                                      pp_model.after_plan,
                                      # u.sort_loads,
                                      **pp_args)
    solution_fitness = u.fitness(solution,
                                 goal,
                                 GOOD_ENOUGH_THRES,
                                 pp_model.after_plan,
                                 **pp_args)
    perf_after_plan = pp_model.after_plan(solution, **pp_args)
    u.print_ea_result(solution, solution_fitness, perf_after_plan, goal)

    '''
    refined_solution = u.acc_small_loads(solution, 0.1)
    solution_fitness = u.fitness(refined_solution,
                                 goal,
                                 GOOD_ENOUGH_THRES,
                                 pp_model.after_plan,
                                 **pp_args)
    perf_after_plan = pp_model.after_plan(refined_solution, **pp_args)
    print('refined solution:')
    u.print_ea_result(refined_solution, solution_fitness, perf_after_plan, goal)
    '''


if __name__ == '__main__':
    ff_parms = {'initial_p': 99.7538,
                'k_1': 3.3266,
                'tau_1': 70.0,
                'k_2': 3.3317,
                'tau_2': 69.5999}
    fitnessfatigue_example(ff_parms)
