from marshmallow import Schema, fields


class UserSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    email = fields.Email()
    role = fields.Str()


class DriveSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    min_cgpa = fields.Float()
    graduation_year = fields.Int()
    deadline = fields.DateTime()
