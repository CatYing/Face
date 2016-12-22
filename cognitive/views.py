# coding=utf-8
import json
import os
from django.http import HttpResponse
from Face import settings
from cognitive.models import *
import httplib
import urllib
# Create your views here.


def add_person(request, name):
    result = {}
    person_name = name
    if Person.objects.filter(name=person_name).count() > 0:
        result['succeeded'] = False
        result['message'] = "Name Existed"
    else:
        upload_path = settings.MEDIA_ROOT + '/existed/'
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        image = request.body
        file_name = upload_path + person_name + '.jpg'
        file_obj = open(file_name, 'wb+')
        file_obj.write(image)
        file_obj.close()
        new_person = Person(
            name=person_name,
            image='http://%s/media/existed/%s' % (settings.HOST_NAME, person_name) + '.jpg'
        )
        new_person.save()
        # 获得此人faceId
        using_info = {}
        using_info['url'] = new_person.image

        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': settings.FACE_KEY,
        }

        params = urllib.urlencode({
            'returnFaceId': 'true',
            'returnFaceLandmarks': 'false',
        })

        conn = httplib.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/face/v1.0/detect?%s" % params, json.dumps(using_info), headers)
        response = json.loads(conn.getresponse().read())
        try:
            face_id = response[0]['faceId']
            new_person.face_id = face_id
            new_person.save()
            result['succeeded'] = True
            result['face_id'] = face_id
        except:
            message = response['error']['message']
            result['succeeded'] = False
            result['message'] = message
        conn.close()

    return HttpResponse(json.dumps(result), content_type='application/json')


def compare(request):
    result = {}
    upload_path = settings.MEDIA_ROOT + '/unknown/'
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    image = request.body
    c = UnknownPerson.objects.all().count()
    file_name = upload_path + 'unknown' + str(c+1) + '.jpg'
    file_obj = open(file_name, 'wb')
    file_obj.write(image)
    file_obj.close()
    new_unknown = UnknownPerson(
        image='http://%s/media/unknown/%s' % (settings.HOST_NAME, "unknown") + str(c+1) + '.jpg'
    )
    new_unknown.save()
    # 获得未知人员的faceId
    using_info = {}
    using_info['url'] = new_unknown.image
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.FACE_KEY,
    }
    params = urllib.urlencode({
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
    })
    conn = httplib.HTTPSConnection('api.projectoxford.ai')
    conn.request("POST", "/face/v1.0/detect?%s" % params, json.dumps(using_info) ,headers)
    response = json.loads(conn.getresponse().read())
    conn.close()
    try:
        face_id = response[0]['faceId']
        new_unknown.face_id = face_id
        new_unknown.save()
        result['up_succeeded'] = True
        result['face_id'] = face_id
    except:
        result['up_succeeded'] = False
        result['up_message'] = response['error']['message']

    # 比较
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.FACE_KEY,
    }
    params = urllib.urlencode({})
    using_info = {}
    if not new_unknown.face_id:
        result['com_succeeded'] = False
        result['com_message'] = "No FaceID"
    else:
        using_info['faceId1'] = new_unknown.face_id
        conn_compare = httplib.HTTPSConnection('api.projectoxford.ai')
        for person in Person.objects.all():
            using_info['faceId2'] = person.face_id
            conn_compare.request("POST", "/face/v1.0/verify?%s" % params, json.dumps(using_info), headers)
            response = json.loads(conn_compare.getresponse().read())
            conn_compare.close()
            if response.has_key("error"):
                result['com_succeeded'] = False
                result['com_message'] = response['error']['message']
                return HttpResponse(json.dumps(result), content_type='application/json')
            else:
                if response['isIdentical']:
                    result['com_succeeded'] = True
                    result['isIdentical'] = response['isIdentical']
                    result['confidence'] = response['confidence']
                    return HttpResponse(json.dumps(result), content_type='application/json')
        result['com_succeeded'] = True
        result['isIdentical'] = response['isIdentical']

    return HttpResponse(json.dumps(result), content_type='application/json')
