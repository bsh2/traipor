from flask import flash, render_template, redirect, url_for
from flask.ext.login import current_user, login_required
from . import main
from .. import db
from ..models import User, FFParameters, PPParameters
from .forms import DeleteGCMetricsFileForm


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/contact')
def contact():
    return render_template('contact.html')


@main.route('/impressum')
def impressum():
    return render_template('impressum.html')


@main.route('/privacy_terms')
def privacy_terms():
    return render_template('privacy_terms.html')


@main.route('/liability_exclusion')
def liability_exclusion():
    return render_template('liability_exclusion.html')


@main.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    user = User.query.filter_by(username=current_user.username).first()
    if user is None:
        return redirect(url_for('main.index'))
    form = DeleteGCMetricsFileForm()

    if form.validate_on_submit():
        db.session.delete(user.gc_metrics_file.first())
        db.session.commit()
        flash('file deleted')
        return redirect(url_for('main.user'))
    return render_template('user.html', user=user, form=form)


@main.route('/ff_playground')
@login_required
def ff_playground():
    default = False
    ff_parms = current_user.ff_parameters.first()
    if ff_parms is None:
        default = True
        ff_parms = FFParameters(initial_p=100,
                                k_1=0.242,
                                tau_1=45.2,
                                k_2=0.372,
                                tau_2=11.3)
    return render_template('ff_playground.html',
                           ff_parms=ff_parms,
                           default=default)


@main.route('/pp_playground')
@login_required
def pp_playground():
    default = False
    pp_parms = current_user.pp_parameters.first()
    if pp_parms is None:
        default = True
        pp_parms = PPParameters(strainpot=0.0,
                                responsepot=0.0,
                                perfpot=0.2,
                                straindelay=6.8,
                                responsedelay=6.3,
                                overflowdelay=0.0)
    return render_template('pp_playground.html',
                           pp_parms=pp_parms,
                           default=default)
