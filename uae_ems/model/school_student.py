import time
import base64
from datetime import date, datetime

from odoo import models, fields, api, _, tools
from odoo.modules import get_module_resource
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import except_orm
from . import school_configuration


class StudentStudent(models.Model):
    ''' Defining a student information '''
    _name = 'student.student'
    _description = 'Student Information'

    @api.model
    def _default_image(self):
        '''Method to get default Image'''
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))

    @api.model
    def check_current_year(self):
        '''Method to get default value of logged in Student'''
        res = self.env['academic.year'].search([('current', '=',
                                                 True)])
        if not res:
            raise ValidationError(_('''There is no current Academic Year defined!Please contact to Administator!'''))
        return res.id

    @api.depends('date_of_birth')
    def _compute_student_age(self):
        '''Method to calculate student age'''
        current_dt = datetime.today()
        for rec in self:
            if rec.date_of_birth:
                start = datetime.strptime(rec.date_of_birth, DEFAULT_SERVER_DATE_FORMAT)
                age_calc = ((current_dt - start).days / 365)
                # Age should be greater than 0
                if age_calc > 0.0:
                    rec.age = age_calc

    @api.model
    def create(self, vals):
        '''Method to create user when student is created'''
        if vals.get('pid', _('New')) == _('New'):
            vals['pid'] = self.env['ir.sequence'
                                   ].next_by_code('student.student'
                                                  ) or _('New')
        if vals.get('pid', False):
            vals['login'] = vals['pid']
            vals['password'] = vals['pid']
        else:
            raise except_orm(_('Error!'),
                             _('''PID not valid
                                 so record will not be saved.'''))
        if vals.get('company_id', False):
            company_vals = {'company_ids': [(4, vals.get('company_id'))]}
            vals.update(company_vals)
        if vals.get('email'):
            school_configuration.emailvalidation(vals.get('email'))
        res = super(StudentStudent, self).create(vals)
        teacher = self.env['school.teacher']
        for data in res.parent_id:
            teacher_rec = teacher.search([('stu_parent_id',
                                           '=', data.id)])
            for record in teacher_rec:
                record.write({'student_id': [(4, res.id, None)]})
        # Assign group to student based on condition
        emp_grp = self.env.ref('base.group_user')
        if res.state == 'draft':
            admission_group = self.env.ref('school.group_is_admission')
            new_grp_list = [admission_group.id, emp_grp.id]
            res.user_id.write({'groups_id': [(6, 0, new_grp_list)]})
        elif res.state == 'done':
            done_student = self.env.ref('school.group_school_student')
            group_list = [done_student.id, emp_grp.id]
            res.user_id.write({'groups_id': [(6, 0, group_list)]})
        return res

    @api.multi
    def write(self, vals):
        teacher = self.env['school.teacher']
        if vals.get('parent_id'):
            for parent in vals.get('parent_id')[0][2]:
                teacher_rec = teacher.search([('stu_parent_id',
                                               '=', parent)])
                for data in teacher_rec:
                    data.write({'student_id': [(4, self.id)]})
        return super(StudentStudent, self).write(vals)

    user_id = fields.Many2one('res.users', 'User ID', ondelete="cascade", required=True, delegate=True)
    student_name = fields.Char('Student Name', related='user_id.name',  store=True, readonly=True)
    pid = fields.Char('Student ID', required=True, default=lambda self: _('New'), help='Personal IDentification Number')
    reg_code = fields.Char('Registration Code', help='Student Registration Code')
    student_code = fields.Char('Student Code')
    contact_phone1 = fields.Char('Phone no.', )
    contact_mobile1 = fields.Char('Mobile no', )
    roll_no = fields.Integer('Roll No.', readonly=True)
    photo = fields.Binary('Photo', default=_default_image)
    year = fields.Many2one('academic.year', 'Academic Year', readonly=True, default=check_current_year)
    cast_id = fields.Many2one('student.cast', 'Religion/Caste')
    relation = fields.Many2one('student.relation.master', 'Relation')
    admission_date = fields.Date('Admission Date', default=fields.Date.today())
    middle = fields.Char('Middle Name', required=True, states={'done': [('readonly', True)]})
    last = fields.Char('Surname', required=True, states={'done': [('readonly', True)]})
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender', states={'done': [('readonly', True)]})
    date_of_birth = fields.Date('BirthDate', required=True,  states={'done': [('readonly', True)]})
    mother_tongue = fields.Many2one('mother.toungue', "Mother Tongue")
    age = fields.Integer(compute='_compute_student_age', string='Age', readonly=True)
    maritual_status = fields.Selection([('unmarried', 'Unmarried'), ('married', 'Married')], 'Marital Status', states={'done': [('readonly', True)]})
    reference_ids = fields.One2many('student.reference', 'reference_id',  'References',  states={'done': [('readonly', True)]})
    previous_school_ids = fields.One2many('student.previous.school', 'previous_school_id', 'Previous School Detail', states={'done': [('readonly', True)]})

    remark = fields.Text('Remark', states={'done': [('readonly', True)]})
    school_id = fields.Many2one('school.school', 'School', states={'done': [('readonly', True)]})
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('terminate', 'Terminate'), ('cancel', 'Cancel'), ('alumni', 'Alumni')], 'State', readonly=True, default="draft")
    history_ids = fields.One2many('student.history', 'student_id', 'History')
    certificate_ids = fields.One2many('student.certificate', 'student_id', 'Certificate')
    student_discipline_line = fields.One2many('student.descipline', 'student_id', 'Descipline')
    document = fields.One2many('student.document', 'doc_id', 'Documents')
    description = fields.One2many('student.description', 'des_id', 'Description')
    student_id = fields.Many2one('student.student', 'Name')
    contact_phone = fields.Char('Phone No', related='student_id.phone', readonly=True)
    contact_mobile = fields.Char('Mobile No', related='student_id.mobile', readonly=True)
    contact_email = fields.Char('Email', related='student_id.email', readonly=True)
    contact_website = fields.Char('WebSite', related='student_id.website', readonly=True)
    award_list = fields.One2many('student.award', 'award_list_id', 'Award List')
    student_status = fields.Selection('Status', related='student_id.state', help="Shows Status Of Student", readonly=True)
    stu_name = fields.Char('First Name', related='user_id.name', readonly=True)
    Acadamic_year = fields.Char('Academic Year', related='year.name', help='Academic Year', readonly=True)
    division_id = fields.Many2one('standard.division', 'Section')
    medium_id = fields.Many2one('standard.medium', 'curriculum')
    cmp_id = fields.Many2one('res.company', 'Company Name', related='school_id.company_id', store=True)
    standard_id = fields.Many2one('school.standard', 'Class')
    parent_ids = fields.Many2many('school.parent', 'students_parents_rel', 'student_id', 'students_parent_id', 'Parent(s)', states={'done': [('readonly', True)]})
    terminate_reason = fields.Text('Reason')
    active = fields.Boolean(default=True)
    teachr_user_grp = fields.Boolean("Teacher Group", compute="_compute_teacher_user")
    active = fields.Boolean(default=True)
    basic_parent_id = fields.Many2one('school.parent', string='Basic Parent')
    discount_ids = fields.Many2many('ems.discount', 'students_discount_rel', 'student_id', 'discount_id', string='Discount')
    # tax_ids = fields.Many2many('account.tax', 'students_taxes_rel', 'students_id', 'tax_id', string="Tax")
    #  ############################### Medical Info ################################
    doctor = fields.Char('Doctor Name')
    designation = fields.Char('Designation')
    doctor_phone = fields.Char('Phone')
    doctor_mobile1 = fields.Char('Mobile 1')
    doctor_mobile2 = fields.Char('Mobile 2')
    doc_description = fields.Text('Description')
    medical_img = fields.Binary(string='Select Medical Image')
    blood_group = fields.Char('Blood Group')
    height = fields.Float('Height', help="Hieght in C.M")
    weight = fields.Float('Weight', help="Weight in K.G")
    eye = fields.Boolean('Eyes')
    ear = fields.Boolean('Ears')
    nose_throat = fields.Boolean('Nose & Throat')
    respiratory = fields.Boolean('Respiratory')
    cardiovascular = fields.Boolean('Cardiovascular')
    neurological = fields.Boolean('Neurological')
    muskoskeletal = fields.Boolean('Musculoskeletal')
    dermatological = fields.Boolean('Dermatological')
    blood_pressure = fields.Boolean('Blood Pressure')
    asthma = fields.Boolean('Asthma')
    diabetes = fields.Boolean('Diabetes')
    heart_problem = fields.Boolean('Heart Problem')
    list_medication = fields.Text(string='List any condition requiring medication')
    tylenol_panadol = fields.Boolean(string='The scghool has permission to administer Tylenol or Panadol')
    wear_glasses = fields.Boolean(string='Does your child wear glasses?')
    eye_examined = fields.Boolean(string='Has an eye specialist examined your child?')
    eye_examined_date = fields.Date(string='If yes, Examined Date')
    hearing_aid = fields.Boolean(string='Does your child has hearing aid?')
    speech_problem = fields.Boolean(string='Does your child has any speech problem?')
    previous_therapy = fields.Boolean(string='Did your child has any previous therapy?')
    previous_therapy_specify = fields.Text(string='Previous Therapy Specify')
    chicken_pox = fields.Boolean('Chicken Pox')
    measles = fields.Boolean('Measles')
    german_measles = fields.Boolean('German Measles')
    mumps = fields.Boolean('Mumps')
    other = fields.Boolean('Other')
    other_name = fields.Char('Other Name')

    # ############################### Others ################################

    mother_name_english = fields.Char('Mother Full English Name')
    mother_name_arabic = fields.Char('Mother Full Arabic Name')
    mother_passport = fields.Char('Mother Passport No')
    mother_nationality = fields.Many2one('res.country', string='Nationality')
    mother_mobile = fields.Char('Mother Mobile No')
    mother_email = fields.Char('Mother Email')
    mother_job_description = fields.Text('Mother Job Description')

    # ############################### Home Address ################################

    home_country_id = fields.Many2one('res.country', string='Country')
    home_city = fields.Char()
    home_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    home_street = fields.Char(string='Street Name')
    home_building_no = fields.Char(sting='Building No')
    zip = fields.Char(change_default=True)
    coordinates = fields.Char(string='Coordinates')

    # ############################### Emergency Info ################################

    emergency_name = fields.Char(string='Name')
    emergency_relationship = fields.Many2one('relationship', string='Relationship')
    emergency_contact1 = fields.Char(string='1st Contact No')
    emergency_contact2 = fields.Char(string='2nd Contact No')

    # ############################### Student State ################################

    student_state = fields.Char(string='Student State')
    student_state_date = fields.Date(string='Date')
    last_year_record_state = fields.Char(string='Last Year Record State')
    current_record_state = fields.Char(string='Current Record State')
    transfer_school = fields.Char(string='Transfer School')
    transfer_date = fields.Char(string='Transfer Date')
    last_result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Last Result')

    # ############################### Information Join To School ################################

    adopt_policy = fields.Boolean(string='Adopt a policy of tuition fees for students according to grade levels')
    join_study_year = fields.Many2one("academic.year", string='Join Study Year')
    join_class = fields.Many2one("school.standard", string='Join Class')

    # ############################### Waiting For Student Entering ################################

    complete_application_form = fields.Boolean(string='Complete Application Form')
    place_and_date_boolean = fields.Boolean(string='Place and Date of Issue')
    place_and_date_char = fields.Char(string='Place and Date of Issue')
    expiry_date_boolean = fields.Boolean(string='Expiry Date')
    expiry_date_char = fields.Char(string='Expiry Date')
    valid_residence_boolean = fields.Boolean(string='Valid Residence')
    expiry_residence_char = fields.Char(string='Valid Residence')
    photo_to_deputy = fields.Boolean(string='Photo to Deputy')
    stamped_signed_by_school = fields.Boolean(string='Stamped And Signed By School')
    authenticated_by_local_education_authority = fields.Boolean(string='Authenticated by Local Education Authority')
    awaiting = fields.Text(string='Awaiting')
    # ##################### Binary fields #############################
    copies_of_child_id = fields.Binary('Copies of Child ID Showing')
    copies_of_child_birth = fields.Binary('Copies of Child Birth Certificate')
    passport_size_photo = fields.Binary('Passport Size Photographs of Child')
    health_form = fields.Binary('Complete Data and Health Forms When Child Is Accepted')
    tranfer_latter = fields.Binary('Transfer Latter/Certificate stating child Previous Class')
    # ##################### Curriculum #############################
    curriculum = fields.Selection([('new_student', 'New Student'), ('transferred', 'Transferred')], string='Curriculum')
    curr_school_name = fields.Char(string='School Name')
    curr_educational_regions = fields.Char(string='Educational Regions')
    curr_last_result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Last School Result')
    curr_detail = fields.Text(string='Details of The Previous Curriculum if Possible')
    family_members = fields.Char(string='Family Members')
    student_order = fields.Char(string='Student Order')
    health_status = fields.Char(string='Health Status')
    cause_of_leakage = fields.Char(string='Cause')
    type_of_help = fields.Char(string='Type Of Help')
    family_income = fields.Char(string='Family Income')
    receipt_card_relief = fields.Char(string='Receipt Card Relief')
    social_status = fields.Char(string='Social Status')

    # ############################### SMS ################################

    sms_mobile1 = fields.Char('Mobile1')
    sms_mobile2 = fields.Char('Mobile2')
    sms_text = fields.Text('SMS Text')
    # sent_msg_ids = fields.One2many('sms.tab', 'student_id', string='Messages sent')

    # ############################### Study History ################################

    # study_history_ids = fields.One2many('study.history.tab', 'student_id', string='Messages sent')

    # ############################### Academic Performance ################################

    # academic_per_ids = fields.One2many('academic.performance', 'student_id', string='Academic Performance')

    # ############################### Attendance ################################

    # attendance_ids = fields.One2many('student.attendance', 'student_id', string='Attendance')

    # ############################### Offence ################################

    # offence_ids = fields.One2many('offence', 'student_id', string='Offence')

    # ############################### Notification ################################

    # notification_ids = fields.One2many('notification', 'student_id', string='Notification')

    # ############################### Immunization Info ################################

    tetanus = fields.Char(string='Tetanus')
    dephtheria = fields.Char(string='Dephtheria')
    polio = fields.Char(string='Polio')
    mmr = fields.Char(string='Measles,Mumps,Rubella (MMR)')
    name_medication = fields.Text(string='Name of Medication')
    dose = fields.Text(string='Dose')
    medicine_for_school = fields.Boolean(string='Will you send medicine for the school to keep?')
    medicine_carry_child = fields.Boolean(string='Do you prefer to have your child carry the medicine with him?')
    medicine_notes = fields.Text(string='Please state any significant medical restriction or pertinent medical info')

    # ############################### Student Details ################################
    student_number = fields.Char(string='Student Number')
    student_type = fields.Many2one('student.type', string='Student Type')
    student_reference_no = fields.Char(string='Reference No')
    student_first_name = fields.Char(string='Student First English Name')
    student_first_name_arabic = fields.Char(string='Student First Arabic Name')
    student_father_full_name = fields.Char(string='Father Full English Name')
    student_father_full_name_arabic = fields.Char(string='Father Full Arabic Name')
    student_id_number = fields.Char(string='ID Number')
    # student_id_issued_place = fields.Char(string='Issued Place')
    student_id_issued_place = fields.Many2one('res.country', string='Issued Place')
    student_id_issued_date = fields.Date(string='Issued Date')
    student_id_expiry_date = fields.Date(string='Expiry Date')
    student_passport_no = fields.Char(string='Passport No')
    # student_passport_issued_place = fields.Char(string='Issued Place')
    student_passport_issued_place = fields.Many2one('res.country', string='Issued Place')
    student_passport_issued_date = fields.Date(string='Issued Date')
    student_passport_expiry_date = fields.Date(string='Expiry Date')
    student_name_in_passport_arabic = fields.Char(string='Name in passport')
    student_name_in_passport_english = fields.Char(string='Name in passport English')
    student_nationality = fields.Many2one('res.country', string='Nationality')
    student_first_language = fields.Many2one('mother.toungue', string="Student's First Language")
    english_knowledge = fields.Selection([('fluent', 'Fluent'), ('adequate', 'Adequate'), ('nil', 'Nil')],
                                         string='Knowledge Of English')
    # student_birth_place = fields.Char(string='Place')
    student_birth_place = fields.Many2one('res.country', string='Place')
    father_education_level = fields.Many2one('education.level', string='Father Education Level')
    mother_education_level = fields.Many2one('education.level', string='Mother Education Level')
    father_employment_place = fields.Char(string='Father Employment Place')
    mother_employment_place = fields.Char(string='Mother Employment Place')
    father_work_tel_no = fields.Char(string='Father Work Tel No')
    mother_work_tel_no = fields.Char(string='Mother Work Tel No')
    father_mobile_no = fields.Char(string='Father Mobile No')
    mother_mobile_no = fields.Char(string='Mother Mobile No')
    father_email = fields.Char(string='Father Email')
    mother_email = fields.Char(string='Mother Email')
    home_address = fields.Text(string='Home Address')
    home_tel_no = fields.Char(string='Home Tel No')
    classification1 = fields.Many2one('classification', string='Student Classification 1')
    classification2 = fields.Many2one('classification', string='Student Classification 2')
    is_registered_noor = fields.Boolean(string='Is Registered Noor')
    noor_registered_no = fields.Char(string='Noor Registered No')
    # ############################### Current Registration ################################
    branch = fields.Many2one('student.branch', string='Branch')
    previously_registered = fields.Boolean(string='Previously Registered')
    arabic_previous_school = fields.Char(string='Arabic Previous School')
    previously_school = fields.Many2one('school.school', string='Previous School')
    previously_class = fields.Many2one('school.standard', string='Previous Class')

    # ############################### Student Payslip ################################

    fee_structure_id = fields.Many2one('student.fees.structure', string="Fee Structure")
    # line_ids = fields.One2many('new.student.fees.structure.line', 'new_student_id', string='Fee Structure Lines')
