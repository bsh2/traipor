import magic
from datetime import date
from flask import render_template, redirect, url_for, flash
from flask.ext.login import login_required
from flask.ext.login import current_user
from . import uploads
from .. import db
from ..models import GCMetricsFile
from .forms import UploadGCMetricsFileForm


def allowed_file_extension(filename):
    '''allow .csv files or files without a filename extension'''
    if '.' not in filename:
        return True
    else:
        return filename.rsplit('.', 1)[1].lower() == 'csv'


def allowed_mime(filecontent):
    return magic.from_buffer(filecontent, mime=True) == b'text/plain'


@uploads.route('/gc_metrics_file', methods=['GET', 'POST'])
@login_required
def gc_metrics_file():
    form = UploadGCMetricsFileForm()
    of = current_user.gc_metrics_file.first()
    if of is None:
        action = 'Upload'
    else:
        action = 'Update'

    if form.validate_on_submit():
        data = form.metrics_file.data
        if data and allowed_file_extension(data.filename):
            rawdata = data.read()
            if not allowed_mime(rawdata):
                flash('Mimetype not allowed.')
                return redirect(url_for('uploads.gc_metrics_file'))
            weekly = form.train_at_limits.data == 'weekly'
            f = GCMetricsFile(data=rawdata,
                              upload_date=date.today(),
                              is_complete=form.is_complete.data,
                              train_weekly_at_limits=weekly,
                              with_power_meter=form.with_power_meter.data,
                              owner_id=current_user.id)
            if of is not None:
                db.session.delete(of)
            db.session.add(f)
            db.session.commit()
            flash(action + ' successfull. Now start your parameter fitting for '
                  'the Fitness Fatigue or PerPot model.')
            return redirect(url_for('main.index'))
        else:
            flash('Filetype not allowed.')
            return redirect(url_for('uploads.gc_metrics_file'))
    return render_template('uploads/gc_metrics_file_upload.html',
                           form=form,
                           action=action)
