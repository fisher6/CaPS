from django import forms

from django.contrib.auth.models import User

from caps.models import *

class RegisterForm(forms.Form):
	username = forms.CharField(max_length=30, label='Andrew ID')
	first_name = forms.CharField(max_length=20)
	last_name = forms.CharField(max_length=20)
	password = forms.CharField(
        max_length=100, widget=forms.PasswordInput)
	confirm_password = forms.CharField(
        max_length=100, widget=forms.PasswordInput)

	def clean(self):
		cleaned_data = super(RegisterForm, self).clean()
		# Confirms that the two password fields match
		password = cleaned_data.get('password')
		confirm_password = cleaned_data.get('confirm_password')
		if password and confirm_password and password != confirm_password:
			raise forms.ValidationError(
                'Passwords do not match', code='unmatching password')
		return cleaned_data

	def clean_username(self): # validates andrewID doesn't exist already
		username_clean = self.cleaned_data.get('username')
		if User.objects.filter(username=username_clean):
			raise forms.ValidationError('AndrewID %(username)s already exists',
			params={'username': username_clean}, code='taken andrewID')
		return username_clean

class UserForm(forms.ModelForm):
    # can't change username - design decision
	username = forms.CharField(
        widget=forms.TextInput(attrs={'readonly':'True'}))
	#email = forms.EmailField()

	class Meta:
		model = User
		fields = ['username', 'first_name', 'last_name']

class StudentForm(forms.ModelForm):
	bio = forms.CharField(widget=forms.Textarea(
        {'cols': 23, 'rows': 6, 'placeholder': 'Tell us about yourself...'}),
        required=False)
	gender = forms.TypedChoiceField(
        choices=GENDER_CHOICES, widget=forms.RadioSelect)
	seeking_help_reasons = forms.ModelMultipleChoiceField(
		widget=forms.CheckboxSelectMultiple,
		queryset=SeekingHelpReason.objects.all(), required=False)
	class_year = forms.TypedChoiceField(
        choices=CLASS_YEAR, widget=forms.RadioSelect)
	class Meta:
		model = Student
		fields = [
            'preferred_name',
            'age',
            'gender',
            'major',
            'seeking_help_reasons',
            'class_year',
            'bio',
            'picture',
		]
		widgets = {
            'picture': forms.FileInput(),
		} # do not let a user remove a picture


class CounselorForm(forms.ModelForm):
	bio = forms.CharField(widget=forms.Textarea(
        {'cols': 23, 'rows': 6, 'placeholder': 'Tell us about yourself...'}),
        required=False)
	gender = forms.TypedChoiceField(
        choices=GENDER_CHOICES, widget=forms.RadioSelect)
	class Meta:
		model = Counselor
		fields = [
            'position_title',
            'age',
            'gender',
            'seniority',
            'degree',
			'school',
            'bio',
			'available',
            'picture',
		]
		widgets = {
            'picture': forms.FileInput(),
		} # do not let a user remove a picture
