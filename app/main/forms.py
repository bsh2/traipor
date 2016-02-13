from flask.ext.wtf import Form
from wtforms import SubmitField


class DeleteGCMetricsFileForm(Form):
    submit = SubmitField('delete')
