import os
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.conf import settings
from utils.views import roundBytes
import shutil


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
	template_name = 'filemanagement/index.html'

	def get_context_data(self, **kwargs):
		context = super(TemplateView, self).get_context_data(**kwargs)
		context['f_total'], context['f_or'], context['f_agent'], context['f_agency'], context['f_client'], context['f_jv'] = get_size()

		if context['f_total'] != 0:
			context['fp_or'] = round(context['f_or'] / context['f_total'] * 100 , 2)
			context['fp_agent'] = round(context['f_agent'] / context['f_total'] * 100 , 2)
			context['fp_agency'] = round(context['f_agency'] / context['f_total'] * 100 , 2)
			context['fp_client'] = round(context['f_client'] / context['f_total'] * 100 , 2)
			context['fp_jv'] = round(context['f_jv'] / context['f_total'] * 100 , 2)

		return context


def get_size(start_path = settings.MEDIA_ROOT):
	f_total = 0
	f_or = 0
	f_agent = 0
	f_agency = 0
	f_client = 0
	f_jv = 0

	for dirpath, dirnames, filenames in os.walk(start_path):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			f_total += os.path.getsize(fp)

			if str(start_path) + '\processing_or' in str(dirpath):
				f_or += os.path.getsize(fp)
			elif str(start_path) + '\processing_data\imported_agent' in str(dirpath):
				f_agent += os.path.getsize(fp)
			elif str(start_path) + '\processing_data\imported_agency' in str(dirpath):
				f_agency += os.path.getsize(fp)
			elif str(start_path) + '\processing_data\imported_client' in str(dirpath):
				f_client += os.path.getsize(fp)
			elif str(start_path) + '\processing_jv' in str(dirpath):
				f_jv += os.path.getsize(fp)


	f_total = roundBytes(f_total, 'mb')
	f_or = roundBytes(f_or, 'mb')
	f_agent = roundBytes(f_agent, 'mb')
	f_agency = roundBytes(f_agency, 'mb')
	f_client = roundBytes(f_client, 'mb')
	f_jv = roundBytes(f_jv, 'mb')

	return f_total, f_or, f_agent, f_agency, f_client, f_jv


def truncateDir(request, path):
	# os.rmdir(settings.MEDIA_ROOT + '/' + path)

	if path == 'imported_agency' or path == 'imported_agent' or path == 'imported_client':
		path = 'processing_data/' + path
		shutil.rmtree(settings.MEDIA_ROOT + '/' + path)
		os.mkdir(settings.MEDIA_ROOT + '/' + path)

	elif path == 'imported_or':
		path = 'processing_or/imported_main' 
		shutil.rmtree(settings.MEDIA_ROOT + '/' + path)
		os.mkdir(settings.MEDIA_ROOT + '/' + path)
		path = 'processing_or/imported_detail' 
		shutil.rmtree(settings.MEDIA_ROOT + '/' + path)
		os.mkdir(settings.MEDIA_ROOT + '/' + path)

	elif path == 'imported_jv':
		path = 'processing_jv/imported_main' 
		shutil.rmtree(settings.MEDIA_ROOT + '/' + path)
		os.mkdir(settings.MEDIA_ROOT + '/' + path)
		path = 'processing_jv/imported_detail' 
		shutil.rmtree(settings.MEDIA_ROOT + '/' + path)
		os.mkdir(settings.MEDIA_ROOT + '/' + path)

	elif path == 'all':
		path = ['processing_data/imported_client', 
				'processing_data/imported_agent', 
				'processing_data/imported_agency', 
				'processing_or/imported_main', 
				'processing_or/imported_detail',
				'processing_jv/imported_main', 
				'processing_jv/imported_detail']
		for data in path:
			shutil.rmtree(settings.MEDIA_ROOT + '/' + data)
			os.mkdir(settings.MEDIA_ROOT + '/' + data)
	else:
		return HttpResponseRedirect('/filemanagement?status=failed')

	return HttpResponseRedirect('/filemanagement?status=success')

