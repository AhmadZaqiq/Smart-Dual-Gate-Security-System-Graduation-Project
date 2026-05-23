from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class EmployeeForm(FlaskForm):
    employee_number = StringField(
        "Employee Number",
        validators=[DataRequired(), Length(max=50)],
    )
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=80)])
    second_name = StringField("Second Name", validators=[DataRequired(), Length(max=80)])
    third_name = StringField("Third Name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=80)])
    rfid_uid = StringField("RFID UID", validators=[Optional(), Length(max=64)])
    fingerprint_position = IntegerField(
        "Fingerprint Position",
        validators=[Optional()],
    )
    face_image_path = StringField("Face Image Path", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save Employee")
