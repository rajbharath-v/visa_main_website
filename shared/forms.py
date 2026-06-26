"""shared/forms.py"""
from django import forms
from .models import Enquiry

_input  = 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
_area   = _input + ' resize-none'


class EnquiryForm(forms.ModelForm):
    class Meta:
        model  = Enquiry
        fields = ['name', 'phone', 'email', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Your name *', 'class': _input}),
            'phone':   forms.TextInput(attrs={'placeholder': 'Phone number *', 'class': _input}),
            'email':   forms.EmailInput(attrs={'placeholder': 'Email (optional)', 'class': _input}),
            'message': forms.Textarea(attrs={'placeholder': 'Any specific requirement? (optional)', 'rows': 3, 'class': _area}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required   = False
        self.fields['message'].required = False
