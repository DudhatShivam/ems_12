from datetime import datetime
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


EM = (r"[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$")


def emailvalidation(email):

    if email:
        EMAIL_REGEX = re.compile(EM)
        if not EMAIL_REGEX.match(email):
            raise ValidationError(_('''This seems not to be valid email.
            Please enter email in correct format!'''))
        else:
            return True


class StudentRelationMaster(models.Model):
    ''' Student Relation Information '''
    _name = "student.relation.master"
    _description = "Student Relation Master"

    name = fields.Char('Name', required=True, help="Enter Relation name")
    seq_no = fields.Integer('Sequence')


class GradeMaster(models.Model):
    _name = 'grade.master'

    name = fields.Char('Grade', required=True)
    grade_ids = fields.One2many('grade.line', 'grade_id', 'Grade Name')


class GradeLine(models.Model):
    _name = 'grade.line'
    _rec_name = 'grade'

    from_mark = fields.Integer('From Marks', required=True,
                               help='The grade will starts from this marks.')
    to_mark = fields.Integer('To Marks', required=True,
                             help='The grade will ends to this marks.')
    grade = fields.Char('Grade', required=True, help="Grade")
    sequence = fields.Integer('Sequence', help="Sequence order of the grade.")
    fail = fields.Boolean('Fail', help='If fail field is set to True,\
                                  it will allow you to set the grade as fail.')
    grade_id = fields.Many2one("grade.master", 'Grade')
    name = fields.Char('Name')


class SchoolSchool(models.Model):
    ''' Defining School Information '''
    _name = 'school.school'
    _description = 'School Information'
    _rec_name = "com_name"

    @api.model
    def _lang_get(self):
        '''Method to get language'''
        languages = self.env['res.lang'].search([])
        return [(language.code, language.name) for language in languages]

    company_id = fields.Many2one('res.company', 'Company',
                                 ondelete="cascade",
                                 required=True,
                                 delegate=True)
    com_name = fields.Char('School Name', related='company_id.name',
                           store=True)
    code = fields.Char('Code', required=True)
    standards = fields.One2many('school.standard', 'school_id',
                                'Standards')
    lang = fields.Selection(_lang_get, 'Language',
                            help='''If the selected language is loaded in the
                                system, all documents related to this partner
                                will be printed in this language.
                                If not, it will be English.''')


class SchoolStandard(models.Model):
    ''' Defining a standard related to school '''
    _name = 'school.standard'
    _description = 'School Standards'

    @api.depends('standard_id', 'school_id', 'division_id', 'medium_id',
                 'school_id')
    def _compute_student(self):
        '''Compute student of done state'''
        student_obj = self.env['student.student']
        for rec in self:
            rec.student_ids = student_obj.\
                search([('standard_id', '=', rec.id),
                        ('school_id', '=', rec.school_id.id),
                        ('division_id', '=', rec.division_id.id),
                        ('medium_id', '=', rec.medium_id.id),
                        ('state', '=', 'done')])

    @api.onchange('standard_id', 'division_id')
    def onchange_combine(self):
        self.name = str(self.standard_id.name
                        ) + '-' + str(self.division_id.name)

    @api.depends('subject_ids')
    def _compute_subject(self):
        '''Method to compute subjects'''
        for rec in self:
            rec.total_no_subjects = len(rec.subject_ids)

    # @api.depends('student_ids')
    # def _compute_total_student(self):
    #     for rec in self:
    #         rec.total_students = len(rec.student_ids)

    @api.depends("capacity", "total_students")
    def _compute_remain_seats(self):
        for rec in self:
            rec.remaining_seats = rec.capacity - rec.total_students

    name = fields.Char(string='Class Name')
    code = fields.Char(string='code')
    school_id = fields.Many2one('school.school', 'School', required=True)
    standard_id = fields.Many2one('standard.standard', 'Standard',
                                  required=True)
    division_id = fields.Many2one('standard.division', 'Division',
                                  required=True)
    medium_id = fields.Many2one('standard.medium', 'Medium', required=True)
    subject_ids = fields.Many2many('subject.subject', 'subject_standards_rel',
                                   'subject_id', 'standard_id', 'Subject')
    # user_id = fields.Many2one('school.teacher', 'Class Teacher')
    #  student_ids = fields.One2many('student.student', 'standard_id',
    #                               'Student In Class',
    #                               compute='_compute_student', store=True
    #                               )
    color = fields.Integer('Color Index')
    cmp_id = fields.Many2one('res.company', 'Company Name',
                             related='school_id.company_id', store=True)
    syllabus_ids = fields.One2many('subject.syllabus', 'standard_id',
                                   'Syllabus')
    total_no_subjects = fields.Integer('Total No of Subject',
                                       compute="_compute_subject")
    name = fields.Char('Name')
    capacity = fields.Integer("Total Seats")
    total_students = fields.Integer("Total Students",
                                    # compute="_compute_total_student",
                                    store=True)
    remaining_seats = fields.Integer("Available Seats",
                                     compute="_compute_remain_seats",
                                     store=True)
    class_room_id = fields.Many2one('class.room', 'Room Number')

    @api.constrains('standard_id', 'division_id')
    def check_standard_unique(self):
        standard_search = self.env['school.standard'
                                   ].search([('standard_id', '=',
                                              self.standard_id.id),
                                             ('division_id', '=',
                                              self.division_id.id),
                                             ('school_id', '=',
                                              self.school_id.id),
                                             ('id', 'not in', self.ids)])
        if standard_search:
            raise ValidationError(_('''Division and class should be unique!'''))

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.student_ids or rec.subject_ids or rec.syllabus_ids:
    #             raise ValidationError(_('''You cannot delete this standard
    #             because it has reference with student or subject or
    #             syllabus!'''))
    #     return super(SchoolStandard, self).unlink()

    @api.constrains('capacity')
    def check_seats(self):
        if self.capacity <= 0:
            raise ValidationError(_('''Total seats should be greater than
                0!'''))

    @api.multi
    def name_get(self):
        '''Method to display standard and division'''
        return [(rec.id, rec.standard_id.name + '[' + rec.division_id.name +
                 ']') for rec in self]


class StandardStandard(models.Model):
    ''' Defining Standard Information '''
    _name = 'standard.standard'
    _description = 'Standard Information'
    _order = "sequence"

    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')

    @api.model
    def next_standard(self, sequence):
        '''This method check sequence of standard'''
        stand_ids = self.search([('sequence', '>', sequence)], order='id',
                                limit=1)
        if stand_ids:
            return stand_ids.id
        return False


class StandardDivision(models.Model):
    ''' Defining a division(A, B, C) related to standard'''
    _name = "standard.division"
    _description = "Standard Division"
    _order = "sequence"

    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')


class StandardMedium(models.Model):
    ''' Defining a medium(ENGLISH, HINDI, GUJARATI) related to standard'''
    _name = "standard.medium"
    _description = "Standard Medium"
    _order = "sequence"

    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')


class SubjectSubject(models.Model):
    '''Defining a subject '''
    _name = "subject.subject"
    _description = "Subjects"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    maximum_marks = fields.Integer("Maximum marks")
    minimum_marks = fields.Integer("Minimum marks")
    weightage = fields.Integer("WeightAge")
    # teacher_ids = fields.Many2many('school.teacher', 'subject_teacher_rel', 'subject_id', 'teacher_id', 'Teachers')
    standard_ids = fields.Many2many('standard.standard',
                                    string='Standards')
    standard_id = fields.Many2one('standard.standard', 'Class')
    is_practical = fields.Boolean('Is Practical',
                                  help='Check this if subject is practical.')
    elective_id = fields.Many2one('subject.elective')
    # student_ids = fields.Many2many('student.student', 'elective_subject_student_rel', 'subject_id', 'student_id', 'Students')


class SubjectElective(models.Model):
    ''' Defining Subject Elective '''
    _name = 'subject.elective'

    name = fields.Char("Name")
    subject_ids = fields.One2many('subject.subject', 'elective_id',
                                  'Elective Subjects')


class SubjectSyllabus(models.Model):
    '''Defining a  syllabus'''
    _name = "subject.syllabus"
    _description = "Syllabus"
    _rec_name = "subject_id"

    standard_id = fields.Many2one('school.standard', 'Standard')
    subject_id = fields.Many2one('subject.subject', 'Subject')
    syllabus_doc = fields.Binary("Syllabus Doc",
                                 help="Attach syllabus related to Subject")


class ClassRoom(models.Model):
    _name = "class.room"

    name = fields.Char("Name")
    number = fields.Char("Room Number")


class MotherTongue(models.Model):
    _name = 'mother.toungue'
    _description = "Mother Toungue"

    name = fields.Char("Mother Tongue")


class StudentReference(models.Model):
    ''' Defining a student reference information '''
    _name = "student.reference"
    _description = "Student Reference"

    reference_id = fields.Many2one('student.student', 'Student')
    name = fields.Char('First Name', required=True)
    middle = fields.Char('Middle Name', required=True)
    last = fields.Char('Surname', required=True)
    designation = fields.Char('Designation', required=True)
    phone = fields.Char('Phone', required=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              'Gender')


class StudentPreviousSchool(models.Model):
    ''' Defining a student previous school information '''
    _name = "student.previous.school"
    _description = "Student Previous School"

    previous_school_id = fields.Many2one('student.student', 'Student')
    name = fields.Char('Name', required=True)
    registration_no = fields.Char('Registration No.', required=True)
    admission_date = fields.Date('Admission Date')
    exit_date = fields.Date('Exit Date')
    course_id = fields.Many2one('standard.standard', 'Course', required=True)
    add_sub = fields.One2many('academic.subject', 'add_sub_id', 'Add Subjects')

    @api.constrains('admission_date', 'exit_date')
    def check_date(self):
        curr_dt = datetime.now()
        new_dt = datetime.strftime(curr_dt, DEFAULT_SERVER_DATE_FORMAT)
        if self.admission_date >= new_dt or self.exit_date >= new_dt:
            raise ValidationError(_('''Your admission date and exit date
            should be less than current date in previous school details!'''))
        if self.admission_date > self.exit_date:
            raise ValidationError(_(''' Admission date should be less than
            exit date in previous school!'''))


class StudentHistory(models.Model):
    _name = "student.history"

    student_id = fields.Many2one('student.student', 'Student')
    academice_year_id = fields.Many2one('academic.year', 'Academic Year',
                                        )
    standard_id = fields.Many2one('school.standard', 'Standard')
    percentage = fields.Float("Percentage", readonly=True)
    result = fields.Char('Result', readonly=True)


class StudentCertificate(models.Model):
    _name = "student.certificate"

    student_id = fields.Many2one('student.student', 'Student')
    description = fields.Char('Description')
    certi = fields.Binary('Certificate', required=True)


class StudentDescipline(models.Model):
    _name = 'student.descipline'

    student_id = fields.Many2one('student.student', 'Student')
    teacher_id = fields.Many2one('school.teacher', 'Teacher')
    date = fields.Date('Date')
    class_id = fields.Many2one('standard.standard', 'Class')
    note = fields.Text('Note')
    action_taken = fields.Text('Action Taken')


class StudentDocument(models.Model):
    _name = 'student.document'
    _rec_name = "doc_type"

    doc_id = fields.Many2one('student.student', 'Student')
    file_no = fields.Char('File No', readonly="1", default=lambda obj: obj.env['ir.sequence'].next_by_code('student.document'))
    submited_date = fields.Date('Submitted Date')
    doc_type = fields.Many2one('document.type', 'Document Type', required=True)
    file_name = fields.Char('File Name',)
    return_date = fields.Date('Return Date')
    new_datas = fields.Binary('Attachments')


class DocumentType(models.Model):
    ''' Defining a Document Type(SSC,Leaving)'''
    _name = "document.type"
    _description = "Document Type"
    _rec_name = "doc_type"
    _order = "seq_no"

    seq_no = fields.Char('Sequence', readonly=True, default=lambda self: _('New'))
    doc_type = fields.Char('Document Type', required=True)

    @api.model
    def create(self, vals):
        if vals.get('seq_no', _('New')) == _('New'):
            vals['seq_no'] = self.env['ir.sequence'].next_by_code('document.type') or _('New')
        return super(DocumentType, self).create(vals)


class StudentDescription(models.Model):
    ''' Defining a Student Description'''
    _name = 'student.description'

    des_id = fields.Many2one('student.student', 'Description')
    name = fields.Char('Name')
    description = fields.Char('Description')


class StudentAward(models.Model):
    _name = 'student.award'
    _description = "Student Awards"

    award_list_id = fields.Many2one('student.student', 'Student')
    name = fields.Char('Award Name')
    description = fields.Char('Description')


class AcademicSubject(models.Model):
    ''' Defining a student previous school information '''
    _name = "academic.subject"
    _description = "Student Previous School"

    add_sub_id = fields.Many2one('student.previous.school', 'Add Subjects',
                                 invisible=True)
    name = fields.Char('Name', required=True)
    maximum_marks = fields.Integer("Maximum marks")
    minimum_marks = fields.Integer("Minimum marks")


class StudentCast(models.Model):
    _name = "student.cast"

    name = fields.Char("Name", required=True)
