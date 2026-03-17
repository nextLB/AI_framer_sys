from django import forms
from .models import RobotDevice


class RobotDeviceForm(forms.ModelForm):
    class Meta:
        model = RobotDevice
        fields = ['device_id', 'name', 'model', 'manufacturer', 'serial_number']
        widgets = {
            'device_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '设备唯一标识'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '设备名称'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '型号'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '制造商'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '序列号'}),
        }