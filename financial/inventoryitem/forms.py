from django import forms
from inventoryitem.models import Inventoryitem

class CreateViewForm(forms.ModelForm):
    code = forms.CharField()

    def clean_code(self):
        code = self.cleaned_data.get('code')
        return code
        # if code == "FA-454-01":
        #     return "error"
        # else:
        #     return "valid"
        # #code_value = self.cleaned_data.get('fieldname')

    class Meta:
        model = Inventoryitem
        fields = ['code', 'description', 'inventoryitemclass', 'unitofmeasure', 'unitcost', 'quantity', 'stocklevel',
                  'expensestatus', 'specialstatus']