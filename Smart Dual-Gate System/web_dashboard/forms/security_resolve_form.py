from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class SecurityResolveForm(FlaskForm):
    notes = StringField("Resolution Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Mark Resolved")
