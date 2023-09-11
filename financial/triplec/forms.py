from django import forms
from .models import TripleC

class ManualDataEntryForm(forms.ModelForm):
    class Meta:
        model = TripleC
        fields = [
            'issue_date', 
            'code', 
            'author_name', 
            'supplier',
            'type', 
            'subtype', 
            'section', 
            'article_title', 
            'no_ccc', 
            'no_items',
            'length1', 
            'length2', 
            'length3',
            'length4', 
            'width1', 
            'width2',
            'width3', 
            'width4', 
            'total_size',
            'rate_code', 
            'amount', 
            'byline', 
        ]