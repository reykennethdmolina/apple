#__author__ = 'reykennethmolina'
from django.contrib.auth.models import Permission
from django.db import connection
from collections import namedtuple, defaultdict, OrderedDict
from itertools import groupby
from module.models import Activitylogs

def usermodule(request):
    userid = 0
    if request.user.is_authenticated():
        userid = request.user.id

    cursor = connection.cursor()
    if request.user.is_superuser:
        #SELECT IF (dct.app_label = 'auth', CONCAT('admin/',dct.app_label, '/', dct.model), dct.app_label) AS app_label, m.code AS modulecode, m.name AS modulename, "
        cursor.execute("SELECT m.segment AS app_label, m.code AS modulecode, m.name AS modulename, "
                       "m.description AS moduledescp, m.segment AS modulesegment, mm.code AS mainmodulecode, "
                       "mm.description AS mainmoduledescp, mm.iconfile AS mainiconfile "
                       "FROM django_content_type AS dct "
                       "INNER JOIN module AS m ON (m.django_content_type_id = dct.id AND m.isdeleted=0)"
                       "LEFT OUTER JOIN mainmodule AS mm ON mm.id = m.mainmodule_id "
                       "WHERE dct.id NOT IN(1,2,5,6) AND mm.isdeleted = 0 AND dct.app_label != '' "
                       "GROUP BY mm.code, dct.model "
                       "ORDER BY mm.sortnumber, m.name")
    else:

        cursor.execute("SELECT * FROM ("
                           "SELECT m.segment AS app_label, m.code AS modulecode, m.name AS modulename, m.description AS moduledescp, "
                           "m.segment AS modulesegment,mm.code AS mainmodulecode, "
                           "mm.description AS mainmoduledescp, mm.iconfile AS mainiconfile, mm.sortnumber, m.name "
                           "FROM auth_user_user_permissions AS auup "
                           "LEFT OUTER JOIN auth_permission AS ap ON ap.id = auup.permission_id "
                           "LEFT OUTER JOIN django_content_type AS dct ON dct.id = ap.content_type_id "
                           "INNER JOIN module AS m ON (m.django_content_type_id = dct.id AND m.isdeleted=0)"
                           "LEFT OUTER JOIN mainmodule AS mm ON mm.id = m.mainmodule_id "
                           "WHERE auup.user_id = "+str(userid)+" "
                           "GROUP BY mm.code, dct.model "
                           "UNION "
                           "SELECT m.segment AS app_label, m.code AS modulecode, m.name AS modulename, m.description AS moduledescp, "
                           "m.segment AS modulesegment,mm.code AS mainmodulecode, mm.description AS mainmoduledescp,"
                           " mm.iconfile AS mainiconfile , mm.sortnumber, m.name	"
                           "FROM auth_user_groups AS aug "
                           "LEFT OUTER JOIN auth_group_permissions AS agp ON agp.group_id = aug.group_id "
                           "LEFT OUTER JOIN auth_permission AS ap ON ap.id = agp.permission_id "
                           "LEFT OUTER JOIN django_content_type AS dct ON dct.id = ap.content_type_id "
                           "INNER JOIN module AS m ON (m.django_content_type_id = dct.id AND m.isdeleted=0)"
                           "LEFT OUTER JOIN mainmodule AS mm ON mm.id = m.mainmodule_id "
                           "WHERE aug.user_id = "+str(userid)+" "
                            "GROUP BY mm.code, dct.model "
                       ") AS mm "
                       "ORDER BY mm.sortnumber, mm.name")
    #userpermission = cursor.fetchall()
    result = namedtuplefetchall(cursor)

    #sortkeyfn = key = lambda s: (s.mainmoduledescp, s.app_label)
    #sortkeymain = sorted(result, key=sortkeyfn, reverse=True) # desc
    #input = sorted(result, key=sortkeyfn)

    #result = []
    #for key, valuesiter in groupby(input, key=sortkeyfn):
    #    result.append(dict(main=key[0], items=list((v[0], v[1], v[2], v[3]) for v in valuesiter)))
    # userpermission = OrderedDict()
    # for p in result:
    #     main = p.mainmoduledescp
    #     icon = p.mainiconfile
    #     #data['applabel'].append(p.app_label)
    #     #data['modulename'] = p.moduledescp
    #     if main not in userpermission:
    #         userpermission[main] = [icon]
    #     userpermission[main].append({p})
    #    # userpermission.append(dict(main=p[0], items=list((v[0], v[1], v[2], v[3]) for v in p)))


    return {
        'userpermission': result,
    }

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def resolver_context_processor(request):
    return {
        'app_name': request.resolver_match.app_name,
        'namespace': request.resolver_match.namespace,
        'url_name': request.resolver_match.url_name
    }