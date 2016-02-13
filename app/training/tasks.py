import numpy as np
import sys
import time

from .. import celeryapp
from .. import db
from ..models import User, FFParameters, PPParameters, FFPlan, PPPlan
from ..models import PendingJob, JobType
from ..email import send_email
from .parameterfitting import ff_minimize_fitting, pp_minimize_fitting
from .parameterfitting import ff_cmaes_fitting, pp_cmaes_fitting
from .parameterfitting import ff_lmfit_fitting, pp_lmfit_fitting
from .fitting_util import plan_perfs_from_dic
from .fitting_util import choose_init_p
from .fitting_util import filter_model_perfs_2_real_perfs, calc_rmse
from .cmaes_planning import genplan as cmaes_genplan
from .cmaes_planning import genplan_de
from .cmaes_planning import genplan_minimize
from .differentialevolution import differential_evolution
from .differentialevolution import POP_SIZE, GOOD_ENOUGH_THRES
from .perpot import performance_over_time as pp_performance_over_time
from . import fitnessfatigue as ff_model
from . import perpot as pp_model
from . import plan_util as u


@celeryapp.task()
def ff_fitting_task(user_id, load_metric, perf_metric, algo):
    user = User.query.get(user_id)
    if user is None:
        print('ff_fitting_task(): no User with user_id {}'.format(user_id))
        return
    if user.has_pending_jobs(JobType.ff_fitting):
        print('ff_fitting_task(): User {} has already pending job '
              'of type ff_fitting'.format(user_id))
        return
    mf = user.gc_metrics_file.first()
    if mf is None:
        print('ff_fitting_task(): '
              'User {} has no gc_metrics_file'.format(user_id))
        return
    try:
        plan, perfs, min_p, plan_since_min_p = \
            _fitting_data(mf, load_metric, perf_metric)
    except:
        print('ff_fitting_task(): {}'.format(sys.exc_info()))
        send_email(user.email,
                   'metrics file can\'t be parsed',
                   '/training/email/metrics_file_parse_error',
                   user=user)
        return
    job = PendingJob(owner_id=user_id, job_type=JobType.ff_fitting)
    db.session.add(job)
    db.session.commit()

    try:
        print('ff_fitting_task() algo = {} load_metric = {}'.
              format(algo, load_metric))
        start_time = int(time.time())
        if algo == 'LEAST_SQUARES':
            # lmfit fitting, defaults to least squares
            optres = ff_lmfit_fitting(plan, perfs)
            initial_p = optres[0][0]
            k_1 = optres[0][1]
            tau_1 = optres[0][2]
            k_2 = optres[0][3]
            tau_2 = optres[0][4]
            rmse = optres[1]
        elif algo == 'DE':
            optres = ff_lmfit_fitting(plan, perfs, 'differential_evolution')
            initial_p = optres[0][0]
            k_1 = optres[0][1]
            tau_1 = optres[0][2]
            k_2 = optres[0][3]
            tau_2 = optres[0][4]
            rmse = optres[1]
        elif algo == 'CMA-ES':
            # cmaes fitting
            optres = ff_cmaes_fitting(plan, perfs)
            initial_p = optres[0][0]
            k_1 = optres[0][1]
            tau_1 = optres[0][2]
            k_2 = optres[0][3]
            tau_2 = optres[0][4]
            rmse = optres[1]
        else:
            # scipy minimize fitting: SLSQP, L-BFGS-B, TNC
            optres = ff_minimize_fitting(plan, perfs, algo)
            print('optres.success {}'.format(optres.success))
            print('optres.message {}'.format(optres.message))
            initial_p = optres.x[0]
            k_1 = optres.x[1]
            tau_1 = optres.x[2]
            k_2 = optres.x[3]
            tau_2 = optres.x[4]
            rmse = optres.fun

        run_time = int(time.time()) - start_time

        # if plan_since_min_p isn't the fitting plan, choose min_p as init_p
        if len(plan_since_min_p) < len(plan):
            initial_p = min_p

        print('rmse {}'.format(rmse))
        print('runtime {}'.format(run_time))
        ffparms = FFParameters(initial_p=initial_p,
                               k_1=k_1,
                               tau_1=tau_1,
                               k_2=k_2,
                               tau_2=tau_2,
                               load_metric=load_metric,
                               perf_metric=perf_metric,
                               plan_since_initial_p=plan_since_min_p,
                               owner_id=user_id)
    except:
        print('ff_fitting_task(): {}'.format(sys.exc_info()))
        db.session.delete(job)
        db.session.commit()
        return

    old_ffparms = user.ff_parameters.first()
    if old_ffparms is not None:
        db.session.delete(old_ffparms)
    db.session.add(ffparms)
    db.session.delete(job)
    db.session.commit()
    send_email(user.email,
               'fitness fatigue parameter fitting done',
               '/training/email/ff_fitting_done_email',
               user=user,
               ffparms=ffparms,
               fmin=rmse,
               runtime=run_time,
               algo=algo)
    return


@celeryapp.task()
def pp_fitting_task(user_id, load_metric, perf_metric, algo):
    user = User.query.get(user_id)
    if user is None:
        print('pp_fitting_task(): no User with user_id {}'.format(user_id))
        return
    if user.has_pending_jobs(JobType.pp_fitting):
        print('pp_fitting_task(): User {} has already pending job '
              'of type pp_fitting'.format(user_id))
        return
    mf = user.gc_metrics_file.first()
    if mf is None:
        print('pp_fitting_task(): '
              'User {} has no gc_metrics_file'.format(user_id))
        return
    try:
        plan, perfs, min_p, plan_since_min_p = \
            _fitting_data(mf, load_metric, perf_metric)
    except:
        print('pp_fitting_task(): {}'.format(sys.exc_info()))
        send_email(user.email,
                   'metrics file can\'t be parsed',
                   '/training/email/metrics_file_parse_error',
                   user=user)
        return
    job = PendingJob(owner_id=user_id, job_type=JobType.pp_fitting)
    db.session.add(job)
    db.session.commit()

    try:
        print('pp_fitting_task() algo = {}'.format(algo))
        start_time = int(time.time())
        if algo == 'LEAST_SQUARES':
            # lmfit fitting, defaults to least squares
            optres, l_scale, perf_scale = pp_lmfit_fitting(plan, perfs)
            perfpot = optres[0][0]
            straindelay = optres[0][1]
            responsedelay = optres[0][2]
            overflowdelay = optres[0][3]
            rmse = optres[1]
        elif algo == 'DE':
            optres, l_scale, perf_scale = \
                pp_lmfit_fitting(plan, perfs, 'differential_evolution')
            perfpot = optres[0][0]
            straindelay = optres[0][1]
            responsedelay = optres[0][2]
            overflowdelay = optres[0][3]
            rmse = optres[1]
        elif algo == 'CMA-ES':
            optres, l_scale, perf_scale = pp_cmaes_fitting(plan, perfs)
            perfpot = optres[0][0]
            straindelay = optres[0][1]
            responsedelay = optres[0][2]
            overflowdelay = optres[0][3]
            rmse = optres[1]
        else:
            # scipy minimize fitting: SLSQP, L-BFGS-B, TNC
            optres, l_scale, perf_scale = pp_minimize_fitting(plan, perfs, algo)
            print('optres.success {}'.format(optres.success))
            print('optres.message {}'.format(optres.message))
            perfpot = optres.x[0]
            straindelay = optres.x[1]
            responsedelay = optres.x[2]
            overflowdelay = optres.x[3]
            rmse = optres.fun

        run_time = int(time.time()) - start_time

        # unscaled rmse calculation
        scaled_plan = list(map(lambda l: l_scale * l, plan))
        model_perfs = pp_performance_over_time(scaled_plan,
                                               0.0,
                                               0.0,
                                               perfpot,
                                               straindelay,
                                               responsedelay,
                                               overflowdelay)
        model_perfs = filter_model_perfs_2_real_perfs(model_perfs, perfs)
        model_perfs = list(map(lambda x: x * perf_scale**-1, model_perfs))
        perfs_measured = list(filter(lambda x: x > 0.0, perfs))
        assert(len(model_perfs) == len(perfs_measured))
        unscaled_rmse = calc_rmse(perfs_measured, model_perfs)

        # if plan_since_min_p isn't the fitting plan, choose min_p as init_p
        if len(plan_since_min_p) < len(plan):
            min_p = perf_scale * min_p
            perfpot = min_p

        print('rmse {}'.format(rmse))
        print('runtime {}'.format(run_time))
        # store scaled values in DB
        plan_since_min_p = list(map(lambda l: l_scale * l, plan_since_min_p))
        ppparms = PPParameters(strainpot=0.0,
                               responsepot=0.0,
                               perfpot=perfpot,
                               straindelay=straindelay,
                               responsedelay=responsedelay,
                               overflowdelay=overflowdelay,
                               load_scale_factor=l_scale,
                               perf_scale_factor=perf_scale,
                               load_metric=load_metric,
                               perf_metric=perf_metric,
                               plan_since_initial_pp=plan_since_min_p,
                               owner_id=user_id)
    except:
        print('pp_fitting_task(): {}'.format(sys.exc_info()))
        db.session.delete(job)
        db.session.commit()
        return

    old_ppparms = user.pp_parameters.first()
    if old_ppparms is not None:
        db.session.delete(old_ppparms)
    db.session.add(ppparms)
    db.session.delete(job)
    db.session.commit()
    send_email(user.email,
               'perpot parameter fitting done',
               '/training/email/pp_fitting_done_email',
               user=user,
               ppparms=ppparms,
               fmin=rmse,
               runtime=run_time,
               algo=algo,
               unscaled_rmse=unscaled_rmse)
    return


@celeryapp.task()
def ff_genplan_task(user_id, plan_req):
    user = User.query.get(user_id)
    if user is None:
        print('ff_genplan_task(): no User with user_id {}'.format(user_id))
        return
    if user.has_pending_jobs(JobType.ff_genplan):
        print('ff_genplan_task(): User {} has already pending job '
              'of type ff_genplan'.format(user_id))
        return
    if plan_req.model_parms is None:
        print('ff_genplan_task(): User {} has no ff_parameters'.format(user_id))
        return

    job = PendingJob(owner_id=user_id, job_type=JobType.ff_genplan)
    db.session.add(job)
    db.session.commit()

    ff_args = plan_req.model_parms.to_dict()
    prequel_plan = plan_req.model_parms.plan_since_initial_p_till_next_monday()
    print('ff_genplan_task(): prequel_plan till monday {}'.format(prequel_plan))
    training_days = u.microcycle_days(plan_req.weekly_cycle,
                                      plan_req.length)
    training_days = u.filter_weeks(training_days, plan_req.off_weeks)
    training_days = u.filter_days(training_days, plan_req.off_days)

    runs = 0
    devisors_to_try = [10, 6, 3, 1]
    pop_init_divisor = devisors_to_try[0]
    best_solution = None
    best_solution_fitness = (-sys.float_info.max, False)
    best_perf_after_plan = 0
    while(not best_solution_fitness[1]):
        solution = differential_evolution(plan_req.length,
                                          plan_req.goal,
                                          training_days,
                                          POP_SIZE,
                                          plan_req.max_load,
                                          plan_req.min_load,
                                          ff_model.after_plan,
                                          prequel_plan=prequel_plan,
                                          pp_func=u.sort_loads,
                                          recomb_weight=0.7,
                                          scale_factor=None,    # dither
                                          pop_init_divisor=pop_init_divisor,
                                          **ff_args)
        prequel_plan_solution = np.concatenate((prequel_plan, solution))
        solution_fitness = u.fitness(prequel_plan_solution,
                                     plan_req.goal,
                                     GOOD_ENOUGH_THRES,
                                     ff_model.after_plan,
                                     **ff_args)
        perf_after_plan = ff_model.after_plan(prequel_plan_solution, **ff_args)
        u.print_ea_result(solution,
                          solution_fitness,
                          perf_after_plan,
                          plan_req.goal)
        if solution_fitness[0] > best_solution_fitness[0]:
            best_solution_fitness = solution_fitness
            best_solution = solution.copy()
            best_perf_after_plan = perf_after_plan
        runs += 1
        if runs < len(devisors_to_try):
            pop_init_divisor = devisors_to_try[runs]
        else:
            break

    weekly_cycle_vals = list(map(lambda d: d.value, plan_req.weekly_cycle))
    ffplan = FFPlan(name=plan_req.name,
                    start_date=plan_req.start_date,
                    start_perf=plan_req.start_perf,
                    end_perf=best_perf_after_plan,
                    loads=best_solution,
                    initial_p=plan_req.model_parms.initial_p,
                    k_1=plan_req.model_parms.k_1,
                    tau_1=plan_req.model_parms.tau_1,
                    k_2=plan_req.model_parms.k_2,
                    tau_2=plan_req.model_parms.tau_2,
                    load_metric=plan_req.model_parms.load_metric,
                    perf_metric=plan_req.model_parms.perf_metric,
                    prequel_plan=prequel_plan,
                    goal=plan_req.goal,
                    length=plan_req.length,
                    max_load=plan_req.max_load,
                    min_load=plan_req.min_load,
                    off_weeks=plan_req.off_weeks,
                    off_days=plan_req.off_days,
                    weekly_cycle=weekly_cycle_vals,
                    owner_id=user.id)
    db.session.add(ffplan)
    db.session.delete(job)
    db.session.commit()

    approx_quality = u.approximation_quality(best_perf_after_plan,
                                             plan_req.goal)
    send_email(user.email,
               'fitness fatigue plan generation done',
               '/training/email/plangen_done_email',
               user=user,
               model='Fitness Fatigue',
               approx_quality=approx_quality,
               below_threshold=solution_fitness[1],
               plan=ffplan)
    return


@celeryapp.task()
def pp_genplan_task(user_id, plan_req):
    user = User.query.get(user_id)
    if user is None:
        print('pp_genplan_task(): no User with user_id {}'.format(user_id))
        return
    if user.has_pending_jobs(JobType.pp_genplan):
        print('pp_genplan_task(): User {} has already pending job '
              'of type pp_genplan'.format(user_id))
        return
    if plan_req.model_parms is None:
        print('pp_genplan_task(): User {} has no pp_parameters'.format(user_id))
        return

    job = PendingJob(owner_id=user_id, job_type=JobType.pp_genplan)
    db.session.add(job)
    db.session.commit()

    pp_args = plan_req.model_parms.to_dict()
    prequel_plan = \
        plan_req.model_parms.plan_since_initial_pp_till_next_monday()
    print('pp_genplan_task(): prequel_plan till monday {}'.format(prequel_plan))
    training_days = u.microcycle_days(plan_req.weekly_cycle,
                                      plan_req.length)
    training_days = u.filter_weeks(training_days, plan_req.off_weeks)
    training_days = u.filter_days(training_days, plan_req.off_days)

    runs = 0
    devisors_to_try = [10, 6, 3, 1]
    pop_init_divisor = devisors_to_try[0]
    best_solution = None
    best_solution_fitness = (-sys.float_info.max, False)
    best_perf_after_plan = 0
    while(not best_solution_fitness[1]):
        print('best_solution_fitness[1] = {}'.format(best_solution_fitness[1]))
        solution = differential_evolution(plan_req.length,
                                          plan_req.goal,
                                          training_days,
                                          POP_SIZE,
                                          plan_req.max_load,
                                          plan_req.min_load,
                                          pp_model.after_plan,
                                          prequel_plan=prequel_plan,
                                          pp_func=u.sort_loads,
                                          recomb_weight=0.7,
                                          scale_factor=None,    # dither
                                          pop_init_divisor=pop_init_divisor,
                                          **pp_args)
        prequel_plan_solution = np.concatenate((prequel_plan, solution))
        solution_fitness = u.fitness(prequel_plan_solution,
                                     plan_req.goal,
                                     GOOD_ENOUGH_THRES,
                                     pp_model.after_plan,
                                     **pp_args)
        perf_after_plan = pp_model.after_plan(prequel_plan_solution, **pp_args)
        u.print_ea_result(solution,
                          solution_fitness,
                          perf_after_plan,
                          plan_req.goal)
        if solution_fitness[0] > best_solution_fitness[0]:
            print('new best_solution_fitness {}'.format(solution_fitness[0]))
            best_solution_fitness = solution_fitness
            best_solution = solution.copy()
            best_perf_after_plan = perf_after_plan
        runs += 1
        if runs < len(devisors_to_try):
            pop_init_divisor = devisors_to_try[runs]
        else:
            break

    weekly_cycle_vals = list(map(lambda d: d.value, plan_req.weekly_cycle))
    ppplan = PPPlan(name=plan_req.name,
                    start_date=plan_req.start_date,
                    start_perf=plan_req.start_perf,
                    end_perf=best_perf_after_plan,
                    loads=best_solution,
                    strainpot=plan_req.model_parms.strainpot,
                    responsepot=plan_req.model_parms.responsepot,
                    perfpot=plan_req.model_parms.perfpot,
                    straindelay=plan_req.model_parms.straindelay,
                    responsedelay=plan_req.model_parms.responsedelay,
                    overflowdelay=plan_req.model_parms.overflowdelay,
                    load_scale_factor=plan_req.model_parms.load_scale_factor,
                    perf_scale_factor=plan_req.model_parms.perf_scale_factor,
                    load_metric=plan_req.model_parms.load_metric,
                    perf_metric=plan_req.model_parms.perf_metric,
                    prequel_plan=prequel_plan,
                    goal=plan_req.goal,
                    length=plan_req.length,
                    max_load=plan_req.max_load,
                    min_load=plan_req.min_load,
                    off_weeks=plan_req.off_weeks,
                    off_days=plan_req.off_days,
                    weekly_cycle=weekly_cycle_vals,
                    owner_id=user.id)
    db.session.add(ppplan)
    db.session.delete(job)
    db.session.commit()

    approx_quality = u.approximation_quality(best_perf_after_plan,
                                             plan_req.goal)
    send_email(user.email,
               'perpot plan generation done',
               '/training/email/plangen_done_email',
               user=user,
               model='PerPot',
               approx_quality=approx_quality,
               below_threshold=best_solution_fitness[1],
               plan=ppplan)
    return


@celeryapp.task()
def ff_genplan_cmaes_task(user_id, plan_req):
    user = User.query.get(user_id)
    if user is None:
        print('ff_genplan_cmaes_task(): no User with user_id {}'.
              ormat(user_id))
        return
    if user.has_pending_jobs(JobType.ff_genplan):
        print('ff_genplan_cmaes_task(): User {} has already pending job '
              'of type ff_genplan'.format(user_id))
        return
    if plan_req.model_parms is None:
        print('ff_genplan_task(): User {} has no ff_parameters'.format(user_id))
        return

    job = PendingJob(owner_id=user_id, job_type=JobType.ff_genplan)
    db.session.add(job)
    db.session.commit()

    ff_args = plan_req.model_parms.to_dict()
    prequel_plan = \
        plan_req.model_parms.plan_since_initial_p_till_next_monday()
    print('ff_genplan_cmaes_task(): prequel_plan till monday {}'.
          format(prequel_plan))
    training_days = u.microcycle_days(plan_req.weekly_cycle,
                                      plan_req.length)
    training_days = u.filter_weeks(training_days, plan_req.off_weeks)
    training_days = u.filter_days(training_days, plan_req.off_days)

    '''solution = genplan_minimize(plan_req.length,
                                plan_req.goal,
                                training_days,
                                plan_req.max_load,
                                ff_model.after_plan,
                                prequel_plan=prequel_plan,
                                pp_func=u.sort_loads,
                                **ff_args).x
    solution = list(solution)'''

    solution = cmaes_genplan(plan_req.length,
                             plan_req.goal,
                             training_days,
                             plan_req.max_load,
                             ff_model.after_plan,
                             prequel_plan=prequel_plan,
                             pp_func=u.sort_loads,
                             **ff_args)
    '''
    solution = genplan_de(plan_req.length,
                          plan_req.goal,
                          training_days,
                          plan_req.max_load,
                          ff_model.after_plan,
                          prequel_plan=prequel_plan,
                          pp_func=u.sort_loads,
                          **ff_args)'''

    solution_fitness = u.fitness(prequel_plan + solution,
                                 plan_req.goal,
                                 GOOD_ENOUGH_THRES,
                                 ff_model.after_plan,
                                 **ff_args)
    perf_after_plan = ff_model.after_plan(prequel_plan + solution, **ff_args)
    u.print_ea_result(solution,
                      solution_fitness,
                      perf_after_plan,
                      plan_req.goal)

    weekly_cycle_vals = list(map(lambda d: d.value, plan_req.weekly_cycle))
    ffplan = FFPlan(name=plan_req.name,
                    start_date=plan_req.start_date,
                    start_perf=plan_req.start_perf,
                    end_perf=perf_after_plan,
                    loads=solution,
                    initial_p=plan_req.model_parms.initial_p,
                    k_1=plan_req.model_parms.k_1,
                    tau_1=plan_req.model_parms.tau_1,
                    k_2=plan_req.model_parms.k_2,
                    tau_2=plan_req.model_parms.tau_2,
                    load_metric=plan_req.model_parms.load_metric,
                    perf_metric=plan_req.model_parms.perf_metric,
                    prequel_plan=prequel_plan,
                    goal=plan_req.goal,
                    length=plan_req.length,
                    max_load=plan_req.max_load,
                    min_load=plan_req.min_load,
                    off_weeks=plan_req.off_weeks,
                    off_days=plan_req.off_days,
                    weekly_cycle=weekly_cycle_vals,
                    owner_id=user.id)
    db.session.add(ffplan)
    db.session.delete(job)
    db.session.commit()

    approx_quality = u.approximation_quality(perf_after_plan, plan_req.goal)
    send_email(user.email,
               'fitness fatigue plan generation done',
               '/training/email/plangen_done_email',
               user=user,
               model='Fitness Fatigue',
               approx_quality=approx_quality,
               below_threshold=solution_fitness[1],
               plan=ffplan)
    return



@celeryapp.task()
def pp_genplan_cmaes_task(user_id, plan_req):
    user = User.query.get(user_id)
    if user is None:
        print('pp_genplan_task(): no User with user_id {}'.format(user_id))
        return
    if user.has_pending_jobs(JobType.pp_genplan):
        print('pp_genplan_task(): User {} has already pending job '
              'of type pp_genplan'.format(user_id))
        return
    if plan_req.model_parms is None:
        print('pp_genplan_task(): User {} has no pp_parameters'.format(user_id))
        return

    job = PendingJob(owner_id=user_id, job_type=JobType.pp_genplan)
    db.session.add(job)
    db.session.commit()

    pp_args = plan_req.model_parms.to_dict()
    prequel_plan = \
        plan_req.model_parms.plan_since_initial_pp_till_next_monday()
    print('pp_genplan_task(): prequel_plan till monday {}'.format(prequel_plan))
    training_days = u.microcycle_days(plan_req.weekly_cycle,
                                      plan_req.length)
    training_days = u.filter_weeks(training_days, plan_req.off_weeks)
    training_days = u.filter_days(training_days, plan_req.off_days)

    '''solution = genplan_minimize(plan_req.length,
                                plan_req.goal,
                                training_days,
                                plan_req.max_load,
                                pp_model.after_plan,
                                prequel_plan=prequel_plan,
                                pp_func=u.sort_loads,
                                **pp_args).x
    solution = list(solution)'''

    solution = cmaes_genplan(plan_req.length,
                             plan_req.goal,
                             training_days,
                             plan_req.max_load,
                             pp_model.after_plan,
                             prequel_plan=prequel_plan,
                             pp_func=u.sort_loads,
                             **pp_args)
    '''
    solution = genplan_de(plan_req.length,
                          plan_req.goal,
                          training_days,
                          plan_req.max_load,
                          pp_model.after_plan,
                          prequel_plan=prequel_plan,
                          pp_func=u.sort_loads,
                          **pp_args)'''

    solution_fitness = u.fitness(prequel_plan + solution,
                                 plan_req.goal,
                                 GOOD_ENOUGH_THRES,
                                 pp_model.after_plan,
                                 **pp_args)
    perf_after_plan = pp_model.after_plan(prequel_plan + solution, **pp_args)
    u.print_ea_result(solution,
                      solution_fitness,
                      perf_after_plan,
                      plan_req.goal)

    weekly_cycle_vals = list(map(lambda d: d.value, plan_req.weekly_cycle))
    ppplan = PPPlan(name=plan_req.name,
                    start_date=plan_req.start_date,
                    start_perf=plan_req.start_perf,
                    end_perf=perf_after_plan,
                    loads=solution,
                    strainpot=plan_req.model_parms.strainpot,
                    responsepot=plan_req.model_parms.responsepot,
                    perfpot=plan_req.model_parms.perfpot,
                    straindelay=plan_req.model_parms.straindelay,
                    responsedelay=plan_req.model_parms.responsedelay,
                    overflowdelay=plan_req.model_parms.overflowdelay,
                    load_scale_factor=plan_req.model_parms.load_scale_factor,
                    perf_scale_factor=plan_req.model_parms.perf_scale_factor,
                    load_metric=plan_req.model_parms.load_metric,
                    perf_metric=plan_req.model_parms.perf_metric,
                    prequel_plan=prequel_plan,
                    goal=plan_req.goal,
                    length=plan_req.length,
                    max_load=plan_req.max_load,
                    min_load=plan_req.min_load,
                    off_weeks=plan_req.off_weeks,
                    off_days=plan_req.off_days,
                    weekly_cycle=weekly_cycle_vals,
                    owner_id=user.id)
    db.session.add(ppplan)
    db.session.delete(job)
    db.session.commit()

    approx_quality = u.approximation_quality(perf_after_plan, plan_req.goal)
    send_email(user.email,
               'perpot plan generation done',
               '/training/email/plangen_done_email',
               user=user,
               model='PerPot',
               approx_quality=approx_quality,
               below_threshold=solution_fitness[1],
               plan=ppplan)
    return


class PlanRequest():
    def __init__(self,
                 name,
                 model_parms,
                 start_date,
                 start_perf,
                 goal,
                 length,  # in weeks
                 max_load,
                 min_load,
                 off_weeks,
                 off_days,
                 weekly_cycle):
        self.name = name
        self.model_parms = model_parms
        self.start_date = start_date
        self.start_perf = start_perf
        self.goal = goal
        self.length = length
        self.max_load = max_load
        self.min_load = min_load
        self.off_weeks = off_weeks
        self.off_days = off_days
        self.weekly_cycle = weekly_cycle


def _fitting_data(mf, load_metric, perf_metric):
    '''parse the metrics file, choose init_p'''
    csvdic = mf.to_csv_dic([load_metric, perf_metric], True)
    plan, perfs, _, _ = plan_perfs_from_dic(csvdic,
                                            load_metric,
                                            perf_metric,
                                            mf.train_weekly_at_limits)
    min_p, plan_since_min_p, perfs_since_min_p = choose_init_p(plan, perfs)
    if len(plan_since_min_p) >= (120):
        plan = plan_since_min_p
        perfs = perfs_since_min_p
    return plan, perfs, min_p, plan_since_min_p
