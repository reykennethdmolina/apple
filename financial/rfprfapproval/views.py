from django.views.generic import ListView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from annoying.functions import get_object_or_None
from requisitionform.models import Rfmain
from companyparameter.models import Companyparameter
from budgetapproverlevels.models import Budgetapproverlevels
from django.db.models import F
from django.contrib.auth.models import User
from purchaserequisitionform.models import Prfmain, Prfdetail
from purchaserequisitionform.views import deleteRfprftransactionitem
from canvasssheet.models import Csdata
from employee.models import Employee
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q
import datetime


@method_decorator(login_required, name='dispatch')
class IndexView(ListView):
    model = Rfmain
    template_name = 'rfprfapproval/index.html'
    context_object_name = 'data_list'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        rfdata = Rfmain.objects.all().filter(isdeleted=0)

        context['rfapprovers'] = User.objects.filter(id__in=set(Rfmain.objects.values_list('designatedapprover',
                                                                                           flat=True))).\
            order_by('first_name')
        # context['prfapprovers'] = User.objects.filter(id__in=set(Prfmain.objects.values_list('designatedapprover',
        #                                                                                      flat=True))).\
        #     order_by('first_name')

        if not self.request.user.has_perm('requisitionform.view_allassignrf'):
            rfdata = rfdata.filter(designatedapprover=self.request.user.id)
            context['rfapprovers'] = context['rfapprovers'].filter(id=self.request.user.id)

        context['rfpending'] = rfdata.filter(rfstatus='F').order_by('enterdate')
        # exclude approved RFs that already have dependent PRFs
        context['rfapproved'] = rfdata.filter(rfstatus='A', totalremainingquantity=F('totalquantity')).\
            order_by('enterdate')
        context['rfdisapproved'] = rfdata.filter(rfstatus='D', status='C').order_by('enterdate')

        # prfdata = Prfmain.objects.all().filter(isdeleted=0, status='A')

        # if not self.request.user.has_perm('purchaserequisitionform.view_allassignprf'):
        #     prfdata = prfdata.filter(designatedapprover=self.request.user.id)
        #     context['prfapprovers'] = context['prfapprovers'].filter(id=self.request.user.id)

        # context['prfpending'] = prfdata.filter(prfstatus='F').order_by('enterdate')

        # exclude approved PRFs that already have dependent CSs (prfmain_id is used in csdata)
        # csdata_exclude = Csdata.objects.filter(isdeleted=0, csmain__isnull=False)
        # context['prfapproved'] = prfdata.filter(prfstatus='A').\
        #     exclude(id__in=set(csdata_exclude.values_list('prfmain', flat=True))).order_by('enterdate')

        # context['prfdisapproved'] = prfdata.filter(prfstatus='D').order_by('enterdate')

        context['formtype'] = 'ALL'
        context['formrfapprover'] = 'ALL'
        context['formprfapprover'] = 'ALL'

        if self.request.method == 'GET':
            if 'selectrfapprover' in self.request.GET:
                if self.request.GET['selectrfapprover'] != 'ALL':
                    context['rfpending'] = context['rfpending'].filter(designatedapprover=self.request.GET['selectrfapprover']).\
                        order_by('enterdate')
                    context['rfapproved'] = context['rfapproved'].filter(designatedapprover=self.request.GET['selectrfapprover']).\
                        order_by('enterdate')
                    context['rfdisapproved'] = context['rfdisapproved'].filter(designatedapprover=self.request.GET['selectrfapprover']).\
                        order_by('enterdate')
                    context['formrfapprover'] = self.request.GET['selectrfapprover']
            # if 'selectprfapprover' in self.request.GET:
            #     if self.request.GET['selectprfapprover'] != 'ALL':
            #         context['prfpending'] = context['prfpending'].filter(designatedapprover=self.request.GET['selectprfapprover']). \
            #             order_by('enterdate')
            #         context['prfapproved'] = context['prfapproved'].filter(designatedapprover=self.request.GET['selectprfapprover']). \
            #             order_by('enterdate')
            #         context['prfdisapproved'] = context['prfdisapproved'].filter(designatedapprover=self.request.GET['selectprfapprover']). \
            #             order_by('enterdate')
            #         context['formprfapprover'] = self.request.GET['selectprfapprover']
            if 'selecttype' in self.request.GET:
                if self.request.GET['selecttype'] == 'RF':
                    context['prfpending'] = context['prfpending'][0:0]
                    context['prfapproved'] = context['prfapproved'][0:0]
                    context['prfdisapproved'] = context['prfdisapproved'][0:0]
                    context['formtype'] = 'RF'
                elif self.request.GET['selecttype'] == 'PRF':
                    context['rfpending'] = context['rfpending'][0:0]
                    context['rfapproved'] = context['rfapproved'][0:0]
                    context['rfdisapproved'] = context['rfdisapproved'][0:0]
                    context['formtype'] = 'PRF'

        if not self.request.user.has_perm('requisitionform.view_assignrf') and not self.request.user.has_perm(
                'requisitionform.view_allassignrf'):
            context['rfpending'] = context['rfpending'][0:0]
            context['rfapproved'] = context['rfapproved'][0:0]
            context['rfdisapproved'] = context['rfdisapproved'][0:0]

        # if not self.request.user.has_perm('purchaserequisitionform.view_assignprf') and not self.request.user.has_perm(
        #         'purchaserequisitionform.view_allassignprf'):
        #     context['prfpending'] = context['prfpending'][0:0]
        #     context['prfapproved'] = context['prfapproved'][0:0]
        #     context['prfdisapproved'] = context['prfdisapproved'][0:0]

        return context


@csrf_exempt
def approve(request):

    if request.method == 'POST':
        # print request.POST['main_id']
        # print request.POST['response']
        # print request.POST['main_type']
        # print request.POST['remarks']

        valid = True

        if request.POST['main_type'] == 'RF':
            if request.POST['response'] == 'A' and request.user.has_perm('requisitionform.can_approverf'):
                approve = Rfmain.objects.get(pk=request.POST['main_id'])
                approve.rfstatus = request.POST['response']
                approve.status = 'A'
            elif request.POST['response'] == 'D' and request.user.has_perm('requisitionform.can_disapproverf'):
                approve = Rfmain.objects.get(pk=request.POST['main_id'])
                approve.rfstatus = request.POST['response']
                approve.isdeleted = 0
                approve.status = 'C'
            else:
                valid = False

        elif request.POST['main_type'] == 'PRF':
            if request.POST['response'] == 'A' and request.user.has_perm('purchaserequisitionform.can_approveprf'):
                approve = Prfmain.objects.get(pk=request.POST['main_id'])
                approve.prfstatus = request.POST['response']
                approve.status = 'A'
            elif request.POST['response'] == 'D' and request.user.has_perm('purchaserequisitionform.can_disapproveprf'):

                # exclude approved PRFs that already have dependent CSs (prfmain_id is used in csdata)
                csdata_exclude = Csdata.objects.filter(isdeleted=0, csmain__isnull=False)
                approve = Prfmain.objects.filter(pk=request.POST['main_id'])\
                    .exclude(id__in=set(csdata_exclude.values_list('prfmain', flat=True))).first()
                approve.prfstatus = request.POST['response']
                approve.status = 'C'

                prfdetail = Prfdetail.objects.filter(prfmain=request.POST['main_id']).exclude(rfmain=None)
                for data in prfdetail:
                    deleteRfprftransactionitem(data)
            else:
                valid = False

        else:
            valid = False

        if valid:
            approve.approverresponse = request.POST['response']
            approve.responsedate = datetime.datetime.now()
            approve.remarks = request.POST['remarks']
            approve.actualapprover = User.objects.get(pk=request.user.id)
            approve.save()

        data = {
            'status': 'success',
            'valid': valid,
        }
    else:
        data = {
            'status': 'error',
        }

    return JsonResponse(data)


@method_decorator(login_required, name='dispatch')
class PrfApprovalView(TemplateView):
    template_name = 'rfprfapproval/prfindex.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        if Companyparameter.objects.filter(budgetapprover=self.request.user).exists():
            context['to_budget'] = Prfmain.objects.filter(prfstatus='F', approverlevel1=None,
                                                          status='A', isdeleted=0).order_by('-prfnum')
        csdata_exclude = Csdata.objects.filter(isdeleted=0, csmain__isnull=False)

        if self.request.method == 'GET' and 'sort' in self.request.GET:
            if self.request.GET['sort'] == 'all':
                context['to_levels'] = Prfmain.objects.filter(status='A', isdeleted=0). \
                    filter(Q(designatedapprover=self.request.user.id) | Q(actualapprover=self.request.user.id)
                           | Q(approverlevel1=self.request.user.id) | Q(approverlevel2=self.request.user.id)
                           | Q(approverlevel3=self.request.user.id) | Q(approverlevel4=self.request.user.id)
                           | Q(approverlevel5=self.request.user.id) | Q(approverlevel6=self.request.user.id))
        else:
            context['to_levels'] = Prfmain.objects.filter(status='A', isdeleted=0).\
                filter((Q(approverlevel_required__gte=1)
                            & Q(approverlevelbudget_response__isnull=False)
                            & Q(approverlevel2_response=None)
                            & ((Q(approverlevel1=self.request.user) | Q(actualapprover=self.request.user)) | (Q(designatedapprover=self.request.user) & Q(actualapprover=None))))
                        | (Q(approverlevel_required__gte=2) & Q(approverlevel1_response='A') & Q(approverlevel3_response=None) & Q(approverlevel2=self.request.user))
                        | (Q(approverlevel_required__gte=3) & Q(approverlevel2_response='A') & Q(approverlevel4_response=None) & Q(approverlevel3=self.request.user))
                        | (Q(approverlevel_required__gte=4) & Q(approverlevel3_response='A') & Q(approverlevel5_response=None) & Q(approverlevel4=self.request.user))
                        | (Q(approverlevel_required__gte=5) & Q(approverlevel4_response='A') & Q(approverlevel6_response=None) & Q(approverlevel5=self.request.user))
                        | (Q(approverlevel_required__gte=6) & Q(approverlevel5_response='A') & Q(approverlevel6=self.request.user)))

        context['to_levels'] = context['to_levels'].exclude(id__in=set(csdata_exclude.values_list('prfmain', flat=True))).order_by('-prfnum')

        context['budgetlevels'] = Budgetapproverlevels.objects.filter(isdeleted=0).order_by('level')
        level2 = Employee.objects.filter(managementlevel=5).values_list('user_id', flat=True)
        context['approverlevel2'] = User.objects.filter(id__in=level2, is_active=1).exclude(username='admin').order_by('first_name')
        level3 = Employee.objects.filter(managementlevel=4).values_list('user_id', flat=True)
        context['approverlevel3'] = User.objects.filter(id__in=level3, is_active=1).exclude(username='admin').order_by('first_name')
        level4 = Employee.objects.filter(managementlevel=3).values_list('user_id', flat=True)
        context['approverlevel4'] = User.objects.filter(id__in=level4, is_active=1).exclude(username='admin').order_by('first_name')
        level5 = Employee.objects.filter(managementlevel=2).values_list('user_id', flat=True)
        context['approverlevel5'] = User.objects.filter(id__in=level5, is_active=1).exclude(username='admin').order_by('first_name')
        level6 = Employee.objects.filter(managementlevel=1).values_list('user_id', flat=True)
        context['approverlevel6'] = User.objects.filter(id__in=level6, is_active=1).exclude(username='admin').order_by('first_name')

        return context


def userprfResponse(request):
    if request.method == 'POST':
        intro_remarks = '<font class="small text-primary">' + str(request.user.first_name) + ' </font><mark class="small text-warning">' + str(datetime.datetime.now().strftime("%m/%d/%y %H:%M")) + '</mark>&nbsp;&nbsp;&nbsp;'

        if request.POST['response_from'] == 'budget':
            if Companyparameter.objects.all().first().budgetapprover.pk == request.user.id \
                    and Prfmain.objects.get(pk=request.POST['response_id'], prfstatus='F',
                                            approverlevel1=None, status='A', isdeleted=0):
                if request.POST['response_type'] == 'a' or request.POST['response_type'] == 'd':
                    prfitem = Prfmain.objects.filter(pk=request.POST['response_id'], status='A', isdeleted=0)

                    if request.POST['response_type'] == 'd' and prfitem.first().approverlevel_required < 6:
                        prfitem.update(approverlevel_required=prfitem.first().approverlevel_required + 1)
                    elif request.POST['response_type'] == 'a' and prfitem.first().approverlevelbudget_response == 'D':
                        prfitem.update(approverlevel_required=prfitem.first().approverlevel_required - 1)

                    prfitem.update(approverlevelbudget=request.user.id,
                                   approverlevelbudget_response=request.POST['response_type'].upper(),
                                   approverlevelbudget_responsedate=datetime.datetime.now())

                    old_remarks = '' if prfitem.first().remarks is None else prfitem.first().remarks
                    prfitem.update(remarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

        elif request.POST['response_from'] == 'levels' and (request.POST['response_type'] == 'a' or request.POST['response_type'] == 'd'):
            csdata_exclude = Csdata.objects.filter(isdeleted=0, csmain__isnull=False)
            prfmain = Prfmain.objects.filter(status='A', isdeleted=0, pk=request.POST['response_id']). \
                filter(Q(designatedapprover=request.user.id) | Q(actualapprover=request.user.id)
                       | Q(approverlevel1=request.user.id) | Q(approverlevel2=request.user.id)
                       | Q(approverlevel3=request.user.id) | Q(approverlevel4=request.user.id)
                       | Q(approverlevel5=request.user.id) | Q(approverlevel6=request.user.id)). \
                exclude(id__in=set(csdata_exclude.values_list('prfmain', flat=True)))

            # check level 1 and assigned
            if prfmain.first().approverlevel_required >= 1 \
                and prfmain.first().approverlevelbudget_response \
                and Employee.objects.filter(user=request.user, managementlevel=6, isdeleted=0, status='A').exists() \
                and prfmain.first().approverlevel2_response is None \
                and ((prfmain.first().approverlevel1 == request.user or prfmain.first().actualapprover == request.user)
                     or (prfmain.first().designatedapprover == request.user and prfmain.first().actualapprover is None)):

                # check if enough approver is supplied
                if request.POST['response_type'] == 'd' \
                   or prfmain.first().approverlevel_required == 1 \
                   or (prfmain.first().approverlevel_required == 2 and request.POST['approvers_panel_2']) \
                   or (prfmain.first().approverlevel_required == 3 and request.POST['approvers_panel_2'] and request.POST['approvers_panel_3']) \
                   or (prfmain.first().approverlevel_required == 4 and request.POST['approvers_panel_2'] and request.POST['approvers_panel_3'] and request.POST['approvers_panel_4']) \
                   or (prfmain.first().approverlevel_required == 5 and request.POST['approvers_panel_2'] and request.POST['approvers_panel_3'] and request.POST['approvers_panel_4'] and request.POST['approvers_panel_5']) \
                   or (prfmain.first().approverlevel_required == 6 and request.POST['approvers_panel_2'] and request.POST['approvers_panel_3'] and request.POST['approvers_panel_4'] and request.POST['approvers_panel_5'] and request.POST['approvers_panel_6']):

                    # save action
                    prfmain.update(actualapprover=request.user,
                                   approverresponse=request.POST['response_type'].upper(),
                                   responsedate=datetime.datetime.now(),
                                   approverlevel1=request.user,
                                   approverlevel1_response=request.POST['response_type'].upper(),
                                   approverlevel1_responsedate=datetime.datetime.now())

                    # save assigned approvers
                    if request.POST['response_type'] == 'a':
                        prfmain.update(approverlevel2=get_object_or_None(User, pk=request.POST['approvers_panel_2'] if request.POST['approvers_panel_2'] else 0),
                                       approverlevel3=get_object_or_None(User, pk=request.POST['approvers_panel_3'] if request.POST['approvers_panel_3'] else 0),
                                       approverlevel4=get_object_or_None(User, pk=request.POST['approvers_panel_4'] if request.POST['approvers_panel_4'] else 0),
                                       approverlevel5=get_object_or_None(User, pk=request.POST['approvers_panel_5'] if request.POST['approvers_panel_5'] else 0),
                                       approverlevel6=get_object_or_None(User, pk=request.POST['approvers_panel_6'] if request.POST['approvers_panel_6'] else 0))

                    # save remarks
                    old_remarks = '' if prfmain.first().remarks is None else prfmain.first().remarks
                    prfmain.update(remarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

                    # check if final step of approval
                    if prfmain.first().approverlevel_required == 1:
                        prfmain.update(prfstatus=request.POST['response_type'].upper())

            # check level 2 and assigned
            elif prfmain.first().approverlevel_required >= 2 \
                and prfmain.first().approverlevel1_response == 'A' \
                and Employee.objects.filter(user=request.user, managementlevel=5, isdeleted=0, status='A').exists() \
                and prfmain.first().approverlevel3_response is None \
                    and prfmain.first().approverlevel2 == request.user:

                # save action
                prfmain.update(approverlevel2=request.user,
                               approverlevel2_response=request.POST['response_type'].upper(),
                               approverlevel2_responsedate=datetime.datetime.now())

                # save remarks
                old_remarks = '' if prfmain.first().remarks is None else prfmain.first().remarks
                prfmain.update(remarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

                # check if final step of approval
                if prfmain.first().approverlevel_required == 2:
                    prfmain.update(prfstatus=request.POST['response_type'].upper())

            # check level 3 and assigned
            elif prfmain.first().approverlevel_required >= 3 \
                and prfmain.first().approverlevel2_response == 'A' \
                and Employee.objects.filter(user=request.user, managementlevel=4, isdeleted=0, status='A').exists() \
                and prfmain.first().approverlevel4_response is None \
                    and prfmain.first().approverlevel3 == request.user:

                # save action
                prfmain.update(approverlevel3=request.user,
                               approverlevel3_response=request.POST['response_type'].upper(),
                               approverlevel3_responsedate=datetime.datetime.now())

                # save remarks
                old_remarks = '' if prfmain.first().remarks is None else prfmain.first().remarks
                prfmain.update(remarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

                # check if final step of approval
                if prfmain.first().approverlevel_required == 3:
                    prfmain.update(prfstatus=request.POST['response_type'].upper())

            # check level 4 and assigned
            elif prfmain.first().approverlevel_required >= 4 \
                and prfmain.first().approverlevel3_response == 'A' \
                and Employee.objects.filter(user=request.user, managementlevel=3, isdeleted=0, status='A').exists() \
                and prfmain.first().approverlevel5_response is None \
                    and prfmain.first().approverlevel4 == request.user:

                # save action
                prfmain.update(approverlevel4=request.user,
                               approverlevel4_response=request.POST['response_type'].upper(),
                               approverlevel4_responsedate=datetime.datetime.now())

                # save remarks
                old_remarks = '' if prfmain.first().remarks is None else prfmain.first().remarks
                prfmain.update(remarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

                # check if final step of approval
                if prfmain.first().approverlevel_required == 4:
                    prfmain.update(prfstatus=request.POST['response_type'].upper())

            # check level 5 and assigned
            elif prfmain.first().approverlevel_required >= 5 \
                and prfmain.first().approverlevel4_response == 'A' \
                and Employee.objects.filter(user=request.user, managementlevel=2, isdeleted=0, status='A').exists() \
                and prfmain.first().approverlevel6_response is None \
                    and prfmain.first().approverlevel5 == request.user:

                # save action
                prfmain.update(approverlevel5=request.user,
                               approverlevel5_response=request.POST['response_type'].upper(),
                               approverlevel5_responsedate=datetime.datetime.now())

                # save remarks
                old_remarks = '' if prfmain.first().remarks is None else prfmain.first().remarks
                prfmain.update(remarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

                # check if final step of approval
                if prfmain.first().approverlevel_required == 5:
                    prfmain.update(prfstatus=request.POST['response_type'].upper())

            # check level 6 and assigned
            elif prfmain.first().approverlevel_required >= 6 \
                and prfmain.first().approverlevel5_response == 'A' \
                and Employee.objects.filter(user=request.user, managementlevel=1, isdeleted=0, status='A').exists() \
                and prfmain.first().approverlevel6 == request.user:

                # save action
                prfmain.update(approverlevel6=request.user,
                               approverlevel6_response=request.POST['response_type'].upper(),
                               approverlevel6_responsedate=datetime.datetime.now())

                # save remarks
                old_remarks = '' if prfmain.first().remarks is None else prfmain.first().remarks
                prfmain.update(remarks=old_remarks + intro_remarks + str(request.POST['response_remarks']) + '</br></br>')

                # check if final step of approval
                if prfmain.first().approverlevel_required == 6:
                    prfmain.update(prfstatus=request.POST['response_type'].upper())

    return HttpResponseRedirect('/rfprfapproval/prf')
