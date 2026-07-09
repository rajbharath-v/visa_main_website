"""shared/forms.py"""
import re
from django import forms
from .models import Enquiry

_input  = 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
_area   = _input + ' resize-none'

SPAM_NAMES = {'roberthip', 'robertpep', 'roberttab', 'robertmup'}


class EnquiryForm(forms.ModelForm):
    # Honeypot — hidden field, bots fill it, humans don't
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'style': 'position:absolute;left:-9999px;top:-9999px;opacity:0;height:0;width:0;',
        'tabindex': '-1',
        'autocomplete': 'off',
    }))

    class Meta:
        model  = Enquiry
        fields = ['name', 'phone', 'email', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Your name *', 'class': _input}),
            'phone':   forms.TextInput(attrs={
                'placeholder': '10-digit number *',
                'class': _input,
                'maxlength': '10',
                'inputmode': 'numeric',
                'pattern': '[0-9]{10}',
            }),
            'email':   forms.EmailInput(attrs={'placeholder': 'Email (optional)', 'class': _input}),
            'message': forms.Textarea(attrs={'placeholder': 'Any specific requirement? (optional)', 'rows': 3, 'class': _area}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required   = False
        self.fields['message'].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7 or len(digits) > 15:
            raise forms.ValidationError('Enter a valid phone number (7–15 digits).')
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('website'):
            raise forms.ValidationError('Bot detected.')
        name = cleaned.get('name', '').strip().lower()
        if name in SPAM_NAMES:
            raise forms.ValidationError('Invalid submission.')
        return cleaned
