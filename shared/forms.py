"""shared/forms.py"""
from django import forms
from .models import Enquiry


class EnquiryForm(forms.ModelForm):
    class Meta:
        model  = Enquiry
        fields = ['name', 'company', 'phone', 'email', 'city',
                  'product_name', 'quantity', 'message']
        widgets = {
            'name':         forms.TextInput(attrs={
                'placeholder': 'Your full name *',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
            }),
            'company':      forms.TextInput(attrs={
                'placeholder': 'Company name',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
            }),
            'phone':        forms.TextInput(attrs={
                'placeholder': 'Phone number *',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
            }),
            'email':        forms.EmailInput(attrs={
                'placeholder': 'Email address *',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
            }),
            'city':         forms.TextInput(attrs={
                'placeholder': 'City',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
            }),
            'product_name': forms.TextInput(attrs={
                'placeholder': 'Product you need',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
            }),
            'quantity':     forms.TextInput(attrs={
                'placeholder': 'Quantity required',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900'
            }),
            'message':      forms.Textarea(attrs={
                'placeholder': 'Describe your requirement...',
                'rows': 4,
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-blue-500 text-sm bg-white text-gray-900 resize-none'
            }),
        }
