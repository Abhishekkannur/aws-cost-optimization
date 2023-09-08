from django import forms

class AWSForm(forms.Form):
    aws_access_key = forms.CharField(label='AWS Access Key', max_length=100)
    aws_secret_key = forms.CharField(label='AWS Secret Key', max_length=100)
    region_name = forms.CharField(label='AWS Region', max_length=100)
