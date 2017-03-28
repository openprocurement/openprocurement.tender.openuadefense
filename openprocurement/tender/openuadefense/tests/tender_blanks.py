# -*- coding: utf-8 -*-
from datetime import timedelta
from openprocurement.tender.openuadefense.models import Tender
from openprocurement.tender.openuadefense.tests.base import test_tender_data
from openprocurement.api.app import ROUTE_PREFIX
from openprocurement.tender.belowthreshold.tests.base import test_organization, test_lots
from openprocurement.tender.core.models import get_now, CPV_ITEMS_CLASS_FROM
from copy import deepcopy


# TenderUATest
def simple_add_tender(self):
    u = Tender(test_tender_data)
    u.tenderID = "UA-X"

    assert u.id is None
    assert u.rev is None

    u.store(self.db)

    assert u.id is not None
    assert u.rev is not None

    fromdb = self.db.get(u.id)

    assert u.tenderID == fromdb['tenderID']
    assert u.doc_type == "Tender"
    assert u.procurementMethodType == "aboveThresholdUA.defense"

    u.delete_instance(self.db)


# TenderUAResourceTest
def empty_listing(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], [])
    self.assertNotIn('{\n    "', response.body)
    self.assertNotIn('callback({', response.body)
    self.assertEqual(response.json['next_page']['offset'], '')
    self.assertNotIn('prev_page', response.json)

    response = self.app.get('/tenders?opt_jsonp=callback')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/javascript')
    self.assertNotIn('{\n    "', response.body)
    self.assertIn('callback({', response.body)

    response = self.app.get('/tenders?opt_pretty=1')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIn('{\n    "', response.body)
    self.assertNotIn('callback({', response.body)

    response = self.app.get('/tenders?opt_jsonp=callback&opt_pretty=1')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/javascript')
    self.assertIn('{\n    "', response.body)
    self.assertIn('callback({', response.body)

    response = self.app.get('/tenders?offset=2015-01-01T00:00:00+02:00&descending=1&limit=10')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], [])
    self.assertIn('descending=1', response.json['next_page']['uri'])
    self.assertIn('limit=10', response.json['next_page']['uri'])
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertIn('limit=10', response.json['prev_page']['uri'])

    response = self.app.get('/tenders?feed=changes')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], [])
    self.assertEqual(response.json['next_page']['offset'], '')
    self.assertNotIn('prev_page', response.json)

    response = self.app.get('/tenders?feed=changes&offset=0', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Offset expired/invalid', u'location': u'params', u'name': u'offset'}
    ])

    response = self.app.get('/tenders?feed=changes&descending=1&limit=10')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], [])
    self.assertIn('descending=1', response.json['next_page']['uri'])
    self.assertIn('limit=10', response.json['next_page']['uri'])
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertIn('limit=10', response.json['prev_page']['uri'])


def listing(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    tenders = []

    for i in range(3):
        offset = get_now().isoformat()
        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        tenders.append(response.json['data'])

    ids = ','.join([i['id'] for i in tenders])

    while True:
        response = self.app.get('/tenders')
        self.assertTrue(ids.startswith(','.join([i['id'] for i in response.json['data']])))
        if len(response.json['data']) == 3:
            break

    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified']))
    self.assertEqual(set([i['id'] for i in response.json['data']]), set([i['id'] for i in tenders]))
    self.assertEqual(set([i['dateModified'] for i in response.json['data']]), set([i['dateModified'] for i in tenders]))
    self.assertEqual([i['dateModified'] for i in response.json['data']], sorted([i['dateModified'] for i in tenders]))

    while True:
        response = self.app.get('/tenders?offset={}'.format(offset))
        self.assertEqual(response.status, '200 OK')
        if len(response.json['data']) == 1:
            break
    self.assertEqual(len(response.json['data']), 1)

    response = self.app.get('/tenders?limit=2')
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('prev_page', response.json)
    self.assertEqual(len(response.json['data']), 2)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 1)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.get('/tenders', params=[('opt_fields', 'status')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified', u'status']))
    self.assertIn('opt_fields=status', response.json['next_page']['uri'])

    response = self.app.get('/tenders', params=[('opt_fields', 'status,enquiryPeriod')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified', u'status', u'enquiryPeriod']))
    self.assertIn('opt_fields=status%2CenquiryPeriod', response.json['next_page']['uri'])

    response = self.app.get('/tenders?descending=1')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified']))
    self.assertEqual(set([i['id'] for i in response.json['data']]), set([i['id'] for i in tenders]))
    self.assertEqual([i['dateModified'] for i in response.json['data']], sorted([i['dateModified'] for i in tenders], reverse=True))

    response = self.app.get('/tenders?descending=1&limit=2')
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 2)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 1)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 0)

    test_tender_data2 = test_tender_data.copy()
    test_tender_data2['mode'] = 'test'
    response = self.app.post_json('/tenders', {'data': test_tender_data2})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    while True:
        response = self.app.get('/tenders?mode=test')
        self.assertEqual(response.status, '200 OK')
        if len(response.json['data']) == 1:
            break
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 1)

    response = self.app.get('/tenders?mode=_all_')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 4)


def listing_changes(self):
    response = self.app.get('/tenders?feed=changes')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    tenders = []

    for i in range(3):
        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        tenders.append(response.json['data'])

    ids = ','.join([i['id'] for i in tenders])

    while True:
        response = self.app.get('/tenders?feed=changes')
        self.assertTrue(ids.startswith(','.join([i['id'] for i in response.json['data']])))
        if len(response.json['data']) == 3:
            break

    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified']))
    self.assertEqual(set([i['id'] for i in response.json['data']]), set([i['id'] for i in tenders]))
    self.assertEqual(set([i['dateModified'] for i in response.json['data']]), set([i['dateModified'] for i in tenders]))
    self.assertEqual([i['dateModified'] for i in response.json['data']], sorted([i['dateModified'] for i in tenders]))

    response = self.app.get('/tenders?feed=changes&limit=2')
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('prev_page', response.json)
    self.assertEqual(len(response.json['data']), 2)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 1)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.get('/tenders?feed=changes', params=[('opt_fields', 'status')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified', u'status']))
    self.assertIn('opt_fields=status', response.json['next_page']['uri'])

    response = self.app.get('/tenders?feed=changes', params=[('opt_fields', 'status,enquiryPeriod')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified', u'status', u'enquiryPeriod']))
    self.assertIn('opt_fields=status%2CenquiryPeriod', response.json['next_page']['uri'])

    response = self.app.get('/tenders?feed=changes&descending=1')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified']))
    self.assertEqual(set([i['id'] for i in response.json['data']]), set([i['id'] for i in tenders]))
    self.assertEqual([i['dateModified'] for i in response.json['data']], sorted([i['dateModified'] for i in tenders], reverse=True))

    response = self.app.get('/tenders?feed=changes&descending=1&limit=2')
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 2)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 1)

    response = self.app.get(response.json['next_page']['path'].replace(ROUTE_PREFIX, ''))
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('descending=1', response.json['prev_page']['uri'])
    self.assertEqual(len(response.json['data']), 0)

    test_tender_data2 = test_tender_data.copy()
    test_tender_data2['mode'] = 'test'
    response = self.app.post_json('/tenders', {'data': test_tender_data2})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    while True:
        response = self.app.get('/tenders?feed=changes&mode=test')
        self.assertEqual(response.status, '200 OK')
        if len(response.json['data']) == 1:
            break
    self.assertEqual(len(response.json['data']), 1)

    response = self.app.get('/tenders?feed=changes&mode=_all_')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 4)


def listing_draft(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    tenders = []
    data = test_tender_data.copy()
    data.update({'status': 'draft'})

    for i in range(3):
        response = self.app.post_json('/tenders', {'data': test_tender_data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        tenders.append(response.json['data'])
        response = self.app.post_json('/tenders', {'data': data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

    ids = ','.join([i['id'] for i in tenders])

    while True:
        response = self.app.get('/tenders')
        self.assertTrue(ids.startswith(','.join([i['id'] for i in response.json['data']])))
        if len(response.json['data']) == 3:
            break

    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(set(response.json['data'][0]), set([u'id', u'dateModified']))
    self.assertEqual(set([i['id'] for i in response.json['data']]), set([i['id'] for i in tenders]))
    self.assertEqual(set([i['dateModified'] for i in response.json['data']]), set([i['dateModified'] for i in tenders]))
    self.assertEqual([i['dateModified'] for i in response.json['data']], sorted([i['dateModified'] for i in tenders]))


def create_tender_invalid(self):
    request_path = '/tenders'
    response = self.app.post(request_path, 'data', status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description':
            u"Content-Type header should be one of ['application/json']", u'location': u'header', u'name': u'Content-Type'}
    ])

    response = self.app.post(
        request_path, 'data', content_type='application/json', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'No JSON object could be decoded',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, 'data', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, {'not_data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, {'data': []}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, {'data': {'procurementMethodType': 'invalid_value'}}, status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not implemented', u'location': u'data', u'name': u'procurementMethodType'}
    ])

    response = self.app.post_json(request_path, {'data': {'invalid_field': 'invalid_value',
                                                 'procurementMethodType': 'aboveThresholdUA.defense'},
                                                }, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Rogue field', u'location':
            u'body', u'name': u'invalid_field'}
    ])

    response = self.app.post_json(request_path, {'data': {'value': 'invalid_value', 'procurementMethodType': 'aboveThresholdUA.defense'},
                                                }, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [
            u'Please use a mapping for this field or Value instance instead of unicode.'], u'location': u'body', u'name': u'value'}
    ])

    response = self.app.post_json(request_path, {'data': {'procurementMethod': 'invalid_value', 'procurementMethodType': 'aboveThresholdUA.defense'}
                                                }, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertIn({u'description': [u"Value must be one of ['open', 'selective', 'limited']."], u'location': u'body', u'name': u'procurementMethod'}, response.json['errors'])
    self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'tenderPeriod'}, response.json['errors'])
    self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'minimalStep'}, response.json['errors'])
    self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'items'}, response.json['errors'])
    # self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'enquiryPeriod'}, response.json['errors'])
    self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'value'}, response.json['errors'])
    self.assertIn({u'description': [u'This field is required.'], u'location': u'body', u'name': u'items'}, response.json['errors'])

    response = self.app.post_json(request_path, {'data': {'enquiryPeriod': {'endDate': 'invalid_value'},
                                                 'procurementMethodType': 'aboveThresholdUA.defense'}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': {u'endDate': [u"Could not parse invalid_value. Should be ISO8601."]}, u'location': u'body', u'name': u'enquiryPeriod'}
    ])

    response = self.app.post_json(request_path, {'data': {'enquiryPeriod': {'endDate': '9999-12-31T23:59:59.999999'},
                                                'procurementMethodType': 'aboveThresholdUA.defense'}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': {u'endDate': [u'date value out of range']}, u'location': u'body', u'name': u'enquiryPeriod'}
    ])

    data = test_tender_data['tenderPeriod']
    test_tender_data['tenderPeriod'] = {'startDate': '2014-10-31T00:00:00', 'endDate': '2014-10-01T00:00:00'}
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data['tenderPeriod'] = data
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': {u'startDate': [u'period should begin before its end']}, u'location': u'body', u'name': u'tenderPeriod'}
    ])

    # data = test_tender_data['tenderPeriod']
    # test_tender_data['tenderPeriod'] = {'startDate': '2014-10-31T00:00:00', 'endDate': '2015-10-01T00:00:00'}
    # response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    # test_tender_data['tenderPeriod'] = data
    # self.assertEqual(response.status, '422 Unprocessable Entity')
    # self.assertEqual(response.content_type, 'application/json')
    # self.assertEqual(response.json['status'], 'error')
    # self.assertEqual(response.json['errors'], [
    #     {u'description': [u'period should begin after enquiryPeriod'], u'location': u'body', u'name': u'tenderPeriod'}
    # ])

    now = get_now()
    test_tender_data['awardPeriod'] = {'startDate': now.isoformat(), 'endDate': now.isoformat()}
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    del test_tender_data['awardPeriod']
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'period should begin after tenderPeriod'], u'location': u'body', u'name': u'awardPeriod'}
    ])

    test_tender_data['auctionPeriod'] = {'startDate': (now + timedelta(days=16)).isoformat(), 'endDate': (now + timedelta(days=16)).isoformat()}
    test_tender_data['awardPeriod'] = {'startDate': (now + timedelta(days=15)).isoformat(), 'endDate': (now + timedelta(days=15)).isoformat()}
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    del test_tender_data['auctionPeriod']
    del test_tender_data['awardPeriod']
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'period should begin after auctionPeriod'], u'location': u'body', u'name': u'awardPeriod'}
    ])

    data = test_tender_data['minimalStep']
    test_tender_data['minimalStep'] = {'amount': '1000.0'}
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data['minimalStep'] = data
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'value should be less than value of tender'], u'location': u'body', u'name': u'minimalStep'}
    ])

    data = test_tender_data['minimalStep']
    test_tender_data['minimalStep'] = {'amount': '100.0', 'valueAddedTaxIncluded': False}
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data['minimalStep'] = data
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'valueAddedTaxIncluded should be identical to valueAddedTaxIncluded of value of tender'], u'location': u'body', u'name': u'minimalStep'}
    ])

    data = test_tender_data['minimalStep']
    test_tender_data['minimalStep'] = {'amount': '100.0', 'currency': "USD"}
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data['minimalStep'] = data
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'currency should be identical to currency of value of tender'], u'location': u'body', u'name': u'minimalStep'}
    ])

    data = test_tender_data["items"][0].pop("additionalClassifications")
    if get_now() > CPV_ITEMS_CLASS_FROM:
        cpv_code = test_tender_data["items"][0]['classification']['id']
        test_tender_data["items"][0]['classification']['id'] = '99999999-9'
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data["items"][0]["additionalClassifications"] = data
    if get_now() > CPV_ITEMS_CLASS_FROM:
        test_tender_data["items"][0]['classification']['id'] = cpv_code
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'additionalClassifications': [u'This field is required.']}], u'location': u'body', u'name': u'items'}
    ])

    data = test_tender_data["items"][0]["additionalClassifications"][0]["scheme"]
    test_tender_data["items"][0]["additionalClassifications"][0]["scheme"] = 'Не ДКПП'
    if get_now() > CPV_ITEMS_CLASS_FROM:
        cpv_code = test_tender_data["items"][0]['classification']['id']
        test_tender_data["items"][0]['classification']['id'] = '99999999-9'
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data["items"][0]["additionalClassifications"][0]["scheme"] = data
    if get_now() > CPV_ITEMS_CLASS_FROM:
        test_tender_data["items"][0]['classification']['id'] = cpv_code
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    if get_now() > CPV_ITEMS_CLASS_FROM:
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'additionalClassifications': [u"One of additional classifications should be one of [ДК003, ДК015, ДК018, specialNorms]."]}], u'location': u'body', u'name': u'items'}
        ])
    else:
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'additionalClassifications': [u"One of additional classifications should be one of [ДКПП, NONE, ДК003, ДК015, ДК018]."]}], u'location': u'body', u'name': u'items'}
        ])

    data = test_organization["contactPoint"]["telephone"]
    del test_tender_data["procuringEntity"]["contactPoint"]["telephone"]
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data["procuringEntity"]["contactPoint"]["telephone"] = data
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': {u'contactPoint': {u'email': [u'telephone or email should be present']}}, u'location': u'body', u'name': u'procuringEntity'}
    ])

    data = test_tender_data["items"][0].copy()
    classification = data['classification'].copy()
    classification["id"] = u'19212310-1'
    data['classification'] = classification
    test_tender_data["items"] = [test_tender_data["items"][0], data]
    response = self.app.post_json(request_path, {'data': test_tender_data}, status=422)
    test_tender_data["items"] = test_tender_data["items"][:1]
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'CPV group of items be identical'], u'location': u'body', u'name': u'items'}
    ])

    data = deepcopy(test_tender_data)
    del data["items"][0]['deliveryDate']
    response = self.app.post_json(request_path, {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
         {u'description': [{u'deliveryDate': [u'This field is required.']}], u'location': u'body', u'name': u'items'}
    ])


def create_tender_generated(self):
    data = test_tender_data.copy()
    #del data['awardPeriod']
    data.update({'id': 'hash', 'doc_id': 'hash2', 'tenderID': 'hash3'})
    response = self.app.post_json('/tenders', {'data': data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    if 'procurementMethodDetails' in tender:
        tender.pop('procurementMethodDetails')
    self.assertEqual(set(tender), set([
        u'procurementMethodType', u'id', u'dateModified', u'tenderID',
        u'status', u'enquiryPeriod', u'tenderPeriod', u'complaintPeriod',
        u'minimalStep', u'items', u'value', u'procuringEntity',
        u'next_check', u'procurementMethod', u'awardCriteria',
        u'submissionMethod', u'auctionPeriod', u'title', u'owner',  u'date',
    ]))
    self.assertNotEqual(data['id'], tender['id'])
    self.assertNotEqual(data['doc_id'], tender['id'])
    self.assertNotEqual(data['tenderID'], tender['tenderID'])


def create_tender_draft(self):
    data = test_tender_data.copy()
    data.update({'status': 'draft'})
    response = self.app.post_json('/tenders', {'data': data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    owner_token = response.json['access']['token']
    self.assertEqual(tender['status'], 'draft')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'value': {'amount': 100}}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u"Can't update tender in current (draft) status", u'location': u'body', u'name': u'data'}
    ])

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'status': 'active.tendering'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    self.assertEqual(tender['status'], 'active.tendering')

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    self.assertEqual(tender['status'], 'active.tendering')


def create_tender(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.post_json('/tenders', {"data": test_tender_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    tender_set = set(tender)
    if 'procurementMethodDetails' in tender_set:
        tender_set.remove('procurementMethodDetails')
    self.assertEqual(tender_set - set(test_tender_data), set([
        u'id', u'dateModified', u'enquiryPeriod', u'auctionPeriod',
        u'complaintPeriod', u'tenderID', u'status', u'procurementMethod',
        u'awardCriteria', u'submissionMethod', u'next_check', u'owner', u'date'
    ]))
    self.assertIn(tender['id'], response.headers['Location'])

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(set(response.json['data']), set(tender))
    self.assertEqual(response.json['data'], tender)

    response = self.app.post_json('/tenders?opt_jsonp=callback', {"data": test_tender_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/javascript')
    self.assertIn('callback({"', response.body)

    response = self.app.post_json('/tenders?opt_pretty=1', {"data": test_tender_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIn('{\n    "', response.body)

    response = self.app.post_json('/tenders', {"data": test_tender_data, "options": {"pretty": True}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIn('{\n    "', response.body)

    data = deepcopy(test_tender_data)
    del data["items"][0]['deliveryAddress']['postalCode']
    del data["items"][0]['deliveryAddress']['locality']
    del data["items"][0]['deliveryAddress']['streetAddress']
    del data["items"][0]['deliveryAddress']['region']
    response = self.app.post_json('/tenders', {'data': data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotIn('postalCode', response.json['data']['items'][0]['deliveryAddress'])
    self.assertNotIn('locality', response.json['data']['items'][0]['deliveryAddress'])
    self.assertNotIn('streetAddress', response.json['data']['items'][0]['deliveryAddress'])
    self.assertNotIn('region', response.json['data']['items'][0]['deliveryAddress'])


def get_tender(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.post_json('/tenders', {'data': test_tender_data})
    self.assertEqual(response.status, '201 Created')
    tender = response.json['data']

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], tender)

    response = self.app.get('/tenders/{}?opt_jsonp=callback'.format(tender['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/javascript')
    self.assertIn('callback({"data": {"', response.body)

    response = self.app.get('/tenders/{}?opt_pretty=1'.format(tender['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIn('{\n    "data": {\n        "', response.body)


def tender_features_invalid(self):
    data = test_tender_data.copy()
    item = data['items'][0].copy()
    item['id'] = "1"
    data['items'] = [item, item.copy()]
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Item id should be uniq for all items'], u'location': u'body', u'name': u'items'}
    ])
    data['items'][0]["id"] = "0"
    data['features'] = [
        {
            "code": "OCDS-123454-AIR-INTAKE",
            "featureOf": "lot",
            "title": u"Потужність всмоктування",
            "enum": [
                {
                    "value": 0.1,
                    "title": u"До 1000 Вт"
                },
                {
                    "value": 0.15,
                    "title": u"Більше 1000 Вт"
                }
            ]
        }
    ]
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'relatedItem': [u'This field is required.']}], u'location': u'body', u'name': u'features'}
    ])
    data['features'][0]["relatedItem"] = "2"
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'relatedItem': [u'relatedItem should be one of lots']}], u'location': u'body', u'name': u'features'}
    ])
    data['features'][0]["featureOf"] = "item"
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'relatedItem': [u'relatedItem should be one of items']}], u'location': u'body', u'name': u'features'}
    ])
    data['features'][0]["relatedItem"] = "1"
    data['features'][0]["enum"][0]["value"] = 0.5
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'enum': [{u'value': [u'Float value should be less than 0.3.']}]}], u'location': u'body', u'name': u'features'}
    ])
    data['features'][0]["enum"][0]["value"] = 0.15
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'enum': [u'Feature value should be uniq for feature']}], u'location': u'body', u'name': u'features'}
    ])
    data['features'][0]["enum"][0]["value"] = 0.1
    data['features'].append(data['features'][0].copy())
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Feature code should be uniq for all features'], u'location': u'body', u'name': u'features'}
    ])
    data['features'][1]["code"] = u"OCDS-123454-YEARS"
    data['features'][1]["enum"][0]["value"] = 0.2
    response = self.app.post_json('/tenders', {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Sum of max value of all features should be less then or equal to 30%'], u'location': u'body', u'name': u'features'}
    ])


def tender_features(self):
    data = test_tender_data.copy()
    item = data['items'][0].copy()
    item['id'] = "1"
    data['items'] = [item]
    data['features'] = [
        {
            "code": "OCDS-123454-AIR-INTAKE",
            "featureOf": "item",
            "relatedItem": "1",
            "title": u"Потужність всмоктування",
            "title_en": u"Air Intake",
            "description": u"Ефективна потужність всмоктування пилососа, в ватах (аероватах)",
            "enum": [
                {
                    "value": 0.05,
                    "title": u"До 1000 Вт"
                },
                {
                    "value": 0.1,
                    "title": u"Більше 1000 Вт"
                }
            ]
        },
        {
            "code": "OCDS-123454-YEARS",
            "featureOf": "tenderer",
            "title": u"Років на ринку",
            "title_en": u"Years trading",
            "description": u"Кількість років, які організація учасник працює на ринку",
            "enum": [
                {
                    "value": 0.05,
                    "title": u"До 3 років"
                },
                {
                    "value": 0.1,
                    "title": u"Більше 3 років"
                }
            ]
        },
        {
            "code": "OCDS-123454-POSTPONEMENT",
            "featureOf": "tenderer",
            "title": u"Відстрочка платежу",
            "title_en": u"Postponement of payment",
            "description": u"Термін відстрочки платежу",
            "enum": [
                {
                    "value": 0.05,
                    "title": u"До 90 днів"
                },
                {
                    "value": 0.1,
                    "title": u"Більше 90 днів"
                }
            ]
        }
    ]
    response = self.app.post_json('/tenders', {'data': data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    self.assertEqual(tender['features'], data['features'])

    response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'features': [{
        "featureOf": "tenderer",
        "relatedItem": None
    }, {}, {}]}})
    self.assertEqual(response.status, '200 OK')
    self.assertIn('features', response.json['data'])
    self.assertNotIn('relatedItem', response.json['data']['features'][0])

    response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'tenderPeriod': {'startDate': None}}})
    self.assertEqual(response.status, '200 OK')
    self.assertIn('features', response.json['data'])

    response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'features': []}})
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('features', response.json['data'])


def patch_tender(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.post_json('/tenders', {'data': test_tender_data})
    self.assertEqual(response.status, '201 Created')
    tender = response.json['data']
    self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']
    dateModified = tender.pop('dateModified')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['status'], 'cancelled')

    response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['status'], 'cancelled')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'procuringEntity': {'kind': 'general'}}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['procuringEntity']['kind'], 'general')

    response = self.app.patch_json('/tenders/{}'.format(tender['id']),
        {'data': {'tenderPeriod': {'startDate': tender['enquiryPeriod']['endDate']}}},
        status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'], [{
            "location": "body",
            "name": "tenderPeriod",
            "description": [
                "tenderPeriod should be greater than 6 working days"
            ]
        }
    ])

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(
        tender['id'], owner_token), {'data': {'procurementMethodRationale': 'Open'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIn('invalidationDate', response.json['data']['enquiryPeriod'])
    new_tender = response.json['data']
    new_enquiryPeriod = new_tender.pop('enquiryPeriod')
    new_dateModified = new_tender.pop('dateModified')
    tender.pop('enquiryPeriod')
    tender['procurementMethodRationale'] = 'Open'
    self.assertEqual(tender, new_tender)
    self.assertNotEqual(dateModified, new_dateModified)

    revisions = self.db.get(tender['id']).get('revisions')
    self.assertTrue(any([i for i in revisions[-1][u'changes'] if i['op'] == u'remove' and i['path'] == u'/procurementMethodRationale']))

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(
        tender['id'], owner_token), {'data': {'dateModified': new_dateModified}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    new_tender2 = response.json['data']
    new_enquiryPeriod2 = new_tender2.pop('enquiryPeriod')
    new_dateModified2 = new_tender2.pop('dateModified')
    self.assertEqual(new_tender, new_tender2)
    self.assertNotEqual(new_enquiryPeriod, new_enquiryPeriod2)
    self.assertNotEqual(new_dateModified, new_dateModified2)

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(
        tender['id'], owner_token), {'data': {'items': [test_tender_data['items'][0]]}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(
        tender['id'], owner_token), {'data': {'items': [{}, test_tender_data['items'][0]]}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    item0 = response.json['data']['items'][0]
    item1 = response.json['data']['items'][1]
    self.assertNotEqual(item0.pop('id'), item1.pop('id'))
    self.assertEqual(item0, item1)

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(
        tender['id'], owner_token), {'data': {'items': [{}]}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(len(response.json['data']['items']), 1)

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'items': [{"classification": {
        "scheme": "CPV",
        "id": "44620000-2",
        "description": "Cartons 2"
    }}]}}, status=200)

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'items': [{"classification": {
        "scheme": "CPV",
        "id": "55523100-3",
        "description": "Послуги з харчування у школах"
    }}]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't change classification")

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'items': [{"additionalClassifications": [
        tender['items'][0]["additionalClassifications"][0] for i in range(3)
    ]}]}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'items': [{"additionalClassifications": tender['items'][0]["additionalClassifications"]}]}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(
        tender['id'], owner_token), {'data': {'enquiryPeriod': {'endDate': new_dateModified2}}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't change enquiryPeriod")

    self.set_status('complete')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'status': 'active.auction'}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update tender in current (complete) status")


def patch_tender_ua(self):
    response = self.app.post_json('/tenders', {'data': test_tender_data})
    self.assertEqual(response.status, '201 Created')
    tender = response.json['data']
    owner_token = response.json['access']['token']
    dateModified = tender.pop('dateModified')
    self.tender_id = tender['id']
    self.go_to_enquiryPeriod_end()

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {"value": {
        "amount": 501,
        "currency": u"UAH"
    }}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "tenderPeriod should be extended by 2 working days")
    tenderPeriod_endDate = get_now() + timedelta(days=7, seconds=10)
    #enquiryPeriod_endDate = tenderPeriod_endDate - timedelta(days=2)
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data':
        {
            "value": {
                "amount": 501,
                "currency": u"UAH"
            },
            "tenderPeriod": {
                "endDate": tenderPeriod_endDate.isoformat()
            }
        }
    })
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['tenderPeriod']['endDate'], tenderPeriod_endDate.isoformat())
    #self.assertEqual(response.json['data']['enquiryPeriod']['endDate'], enquiryPeriod_endDate.isoformat())


def dateModified_tender(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.post_json('/tenders', {'data': test_tender_data})
    self.assertEqual(response.status, '201 Created')
    tender = response.json['data']
    dateModified = tender['dateModified']

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['dateModified'], dateModified)

    response = self.app.patch_json('/tenders/{}'.format(
        tender['id']), {'data': {'procurementMethodRationale': 'Open'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotEqual(response.json['data']['dateModified'], dateModified)
    tender = response.json['data']
    dateModified = tender['dateModified']

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], tender)
    self.assertEqual(response.json['data']['dateModified'], dateModified)


def tender_not_found(self):
    response = self.app.get('/tenders')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(len(response.json['data']), 0)

    response = self.app.get('/tenders/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
    ])

    response = self.app.patch_json(
        '/tenders/some_id', {'data': {}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
    ])


def tender_Administrator_change(self):
    response = self.app.post_json('/tenders', {'data': test_tender_data})
    self.assertEqual(response.status, '201 Created')
    tender = response.json['data']

    response = self.app.post_json('/tenders/{}/questions'.format(tender['id']), {'data': {'title': 'question title', 'description': 'question description', 'author': test_organization}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    question = response.json['data']

    authorization = self.app.authorization
    self.app.authorization = ('Basic', ('administrator', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'mode': u'test', 'procuringEntity': {"identifier":{"id": "00000000"}}}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['mode'], u'test')
    self.assertEqual(response.json['data']["procuringEntity"]["identifier"]["id"], "00000000")

    response = self.app.patch_json('/tenders/{}/questions/{}'.format(tender['id'], question['id']), {"data": {"answer": "answer"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'], [
        {"location": "url", "name": "role", "description": "Forbidden"}
    ])
    self.app.authorization = authorization

    response = self.app.post_json('/tenders', {'data': test_tender_data})
    self.assertEqual(response.status, '201 Created')
    tender = response.json['data']

    response = self.app.post_json('/tenders/{}/cancellations'.format(tender['id']), {'data': {'reason': 'cancellation reason', 'status': 'active'}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')

    self.app.authorization = ('Basic', ('administrator', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender['id']), {'data': {'mode': u'test'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['mode'], u'test')


def invalid_bid_tender_features(self):
    self.app.authorization = ('Basic', ('broker', ''))
    # empty tenders listing
    response = self.app.get('/tenders')
    self.assertEqual(response.json['data'], [])
    # create tender
    data = deepcopy(test_tender_data)
    data['features'] = [
        {
            "code": "OCDS-123454-POSTPONEMENT",
            "featureOf": "tenderer",
            "title": u"Відстрочка платежу",
            "description": u"Термін відстрочки платежу",
            "enum": [
                {
                    "value": 0.05,
                    "title": u"До 90 днів"
                },
                {
                    "value": 0.1,
                    "title": u"Більше 90 днів"
                }
            ]
        }
    ]
    response = self.app.post_json('/tenders',
                                  {"data": data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    tender_id = self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']

    # create bid
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'selfEligible': True, 'selfQualified': True,
                                            'parameters': [{"code": "OCDS-123454-POSTPONEMENT" ,"value": 0.1}],
                                            'tenderers': [test_organization], "value": {"amount": 500}}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    bid_id = response.json['data']['id']
    bid_token = response.json['access']['token']

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"features": [{"code": "OCDS-123-POSTPONEMENT"}]}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual("OCDS-123-POSTPONEMENT", response.json['data']["features"][0]["code"])

    response = self.app.patch_json('/tenders/{}/bids/{}?acc_token={}'.format(tender_id, bid_id, bid_token),
                                  {'data': {'parameters': [{"code": "OCDS-123-POSTPONEMENT"}],
                                            'status': 'active'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual("OCDS-123-POSTPONEMENT", response.json['data']["parameters"][0]["code"])

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"features": [{"enum": [{"value": 0.2}]}]}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(0.2, response.json['data']["features"][0]["enum"][0]["value"])

    response = self.app.patch_json('/tenders/{}/bids/{}?acc_token={}'.format(tender_id, bid_id, bid_token),
                                  {'data': {'parameters': [{"value": 0.2}],
                                            'status': 'active'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual("OCDS-123-POSTPONEMENT", response.json['data']["parameters"][0]["code"])

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"features": []}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertNotIn("features",response.json['data'])

    # switch to active.qualification
    self.set_status('active.auction', {"auctionPeriod": {"startDate": None}, 'status': 'active.tendering'})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
    self.assertEqual(response.json['data']['status'], 'unsuccessful')
    self.assertNotEqual(response.json['data']['date'], tender['date'])


def invalid_bid_tender_lot(self):
    self.app.authorization = ('Basic', ('broker', ''))
    # empty tenders listing
    response = self.app.get('/tenders')
    self.assertEqual(response.json['data'], [])
    # create tender
    response = self.app.post_json('/tenders', {"data": test_tender_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    tender = response.json['data']
    tender_id = self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']

    lots = []
    for lot in test_lots * 2:
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': lot})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lots.append(response.json['data']['id'])

    # create bid
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'selfEligible': True, 'selfQualified': True,
                                            'status': 'draft',
                                            'lotValues': [{"value": {"amount": 500}, 'relatedLot': i} for i in lots],
                                            'tenderers': [test_organization]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    bid_id = response.json['data']['id']
    bid_token = response.json['access']['token']

    response = self.app.delete('/tenders/{}/lots/{}?acc_token={}'.format(tender_id, lots[0], owner_token))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    # switch to active.qualification
    self.set_status('active.auction', {"auctionPeriod": {"startDate": None}, 'status': 'active.tendering'})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
    self.assertEqual(response.json['data']['status'], 'unsuccessful')
    self.assertNotEqual(response.json['data']['date'], tender['date'])


# TenderUAProcessTest
def invalid_tender_conditions(self):
    self.app.authorization = ('Basic', ('broker', ''))
    # empty tenders listing
    response = self.app.get('/tenders')
    self.assertEqual(response.json['data'], [])
    # create tender
    response = self.app.post_json('/tenders',
                                  {"data": test_tender_data})
    tender_id = self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']
    # switch to active.tendering
    self.set_status('active.tendering')
    # create compaint
    # self.app.authorization = ('Basic', ('token', ''))
    # response = self.app.post_json('/tenders/{}/complaints'.format(tender_id),
    #                               {'data': {'title': 'invalid conditions', 'description': 'description', 'author': test_organization}})
    # complaint_id = response.json['data']['id']
    # complaint_owner_token = response.json['access']['token']
    # # answering claim
    # self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(tender_id, complaint_id, owner_token), {"data": {
    #     "status": "answered",
    #     "resolutionType": "resolved",
    #     "resolution": "I will cancel the tender"
    # }})
    # # satisfying resolution
    # self.app.patch_json('/tenders/{}/complaints/{}?acc_token={}'.format(tender_id, complaint_id, complaint_owner_token), {"data": {
    #     "satisfied": True,
    #     "status": "resolved"
    # }})
    # cancellation
    self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(tender_id, owner_token), {'data': {
        'reason': 'invalid conditions',
        'status': 'active'
    }})
    # check status
    response = self.app.get('/tenders/{}'.format(tender_id))
    self.assertEqual(response.json['data']['status'], 'cancelled')


def one_valid_bid_tender_ua(self):
    self.app.authorization = ('Basic', ('broker', ''))
    # empty tenders listing
    response = self.app.get('/tenders')
    self.assertEqual(response.json['data'], [])
    # create tender
    response = self.app.post_json('/tenders',
                                  {"data": test_tender_data})
    tender_id = self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']
    # switch to active.tendering XXX temporary action.
    response = self.set_status('active.tendering', {"auctionPeriod": {"startDate": (get_now() + timedelta(days=16)).isoformat()}})
    self.assertIn("auctionPeriod", response.json['data'])


    # create bid
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'tenderers': [test_organization], "value": {"amount": 500}, 'selfEligible': True, 'selfQualified': True}})

    bid_id = self.bid_id = response.json['data']['id']


    # switch to active.qualification
    self.set_status('active.auction', {"auctionPeriod": {"startDate": None}, 'status': 'active.tendering'})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
    self.assertEqual(response.json['data']['status'], 'active.qualification')


def one_invalid_bid_tender(self):
    self.app.authorization = ('Basic', ('broker', ''))
    # empty tenders listing
    response = self.app.get('/tenders')
    self.assertEqual(response.json['data'], [])
    # create tender
    response = self.app.post_json('/tenders',
                                  {"data": test_tender_data})
    tender_id = self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']
    # create bid
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'tenderers': [test_organization], "value": {"amount": 500}, 'selfEligible': True, 'selfQualified': True}})
    # switch to active.qualification
    self.set_status('active.auction', {"auctionPeriod": {"startDate": None}, 'status': 'active.tendering'})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
    # get awards
    self.assertEqual(response.json['data']['status'], 'active.qualification')
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
    # get pending award
    award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
    # set award as unsuccessful
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token),
                                   {"data": {"status": "unsuccessful"}})
    # time travel
    tender = self.db.get(tender_id)
    for i in tender.get('awards', []):
        i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
    self.db.save(tender)
    # set tender status after stand slill period
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
    # check status
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}'.format(tender_id))
    self.assertEqual(response.json['data']['status'], 'unsuccessful')


def first_bid_tender(self):
    self.app.authorization = ('Basic', ('broker', ''))
    # empty tenders listing
    response = self.app.get('/tenders')
    self.assertEqual(response.json['data'], [])
    # create tender
    response = self.app.post_json('/tenders',
                                  {"data": test_tender_data})
    tender_id = self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']
    # switch to active.tendering
    self.set_status('active.tendering')
    # create bid
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'tenderers': [test_organization], "value": {"amount": 450}, 'selfEligible': True, 'selfQualified': True}})
    bid_id = response.json['data']['id']
    bid_token = response.json['access']['token']
    # create second bid
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'tenderers': [test_organization], "value": {"amount": 475}, 'selfEligible': True, 'selfQualified': True}})
    # switch to active.auction
    self.set_status('active.auction')

    # get auction info
    self.app.authorization = ('Basic', ('auction', ''))
    response = self.app.get('/tenders/{}/auction'.format(tender_id))
    auction_bids_data = response.json['data']['bids']
    # posting auction urls
    response = self.app.patch_json('/tenders/{}/auction'.format(tender_id),
                                   {
                                       'data': {
                                           'auctionUrl': 'https://tender.auction.url',
                                           'bids': [
                                               {
                                                   'id': i['id'],
                                                   'participationUrl': 'https://tender.auction.url/for_bid/{}'.format(i['id'])
                                               }
                                               for i in auction_bids_data
                                           ]
                                       }
    })
    # view bid participationUrl
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/bids/{}?acc_token={}'.format(tender_id, bid_id, bid_token))
    self.assertEqual(response.json['data']['participationUrl'], 'https://tender.auction.url/for_bid/{}'.format(bid_id))

    # posting auction results
    self.app.authorization = ('Basic', ('auction', ''))
    response = self.app.post_json('/tenders/{}/auction'.format(tender_id),
                                  {'data': {'bids': auction_bids_data}})
    # get awards
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
    # get pending award
    award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
    # set award as unsuccessful
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token),
                                   {"data": {"status": "unsuccessful"}})
    # get awards
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
    # get pending award
    award2_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
    self.assertNotEqual(award_id, award2_id)
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
    # get pending award
    award2_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
    self.assertNotEqual(award_id, award2_id)
    # create first award complaint
    # get awards
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
    # get pending award
    award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
    # set award as active
    self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active", "qualified": True, "eligible": True}})
    # get contract id
    response = self.app.get('/tenders/{}'.format(tender_id))
    contract_id = response.json['data']['contracts'][-1]['id']
    # create tender contract document for test
    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(tender_id, contract_id, owner_token), upload_files=[('file', 'name.doc', 'content')], status=201)
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    # after stand slill period
    self.app.authorization = ('Basic', ('chronograph', ''))
    self.set_status('complete', {'status': 'active.awarded'})
    # time travel
    tender = self.db.get(tender_id)
    for i in tender.get('awards', []):
        i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
    self.db.save(tender)
    # sign contract
    self.app.authorization = ('Basic', ('broker', ''))
    self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
    # check status
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}'.format(tender_id))
    self.assertEqual(response.json['data']['status'], 'complete')

    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(tender_id, contract_id, owner_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")

    response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(tender_id, contract_id, doc_id, owner_token), {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(tender_id, contract_id, doc_id, owner_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")


def lost_contract_for_active_award(self):
    self.app.authorization = ('Basic', ('broker', ''))
    # create tender
    response = self.app.post_json('/tenders',
                                  {"data": test_tender_data})
    tender_id = self.tender_id = response.json['data']['id']
    owner_token = response.json['access']['token']
    # create bid
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'selfEligible': True, 'selfQualified': True,
                                            'tenderers': [test_organization], "value": {"amount": 450}}})
    # create bid #2
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                  {'data': {'selfEligible': True, 'selfQualified': True,
                                            'tenderers': [test_organization], "value": {"amount": 450}}})
    # switch to active.auction
    self.set_status('active.auction')

    # get auction info
    self.app.authorization = ('Basic', ('auction', ''))
    response = self.app.get('/tenders/{}/auction'.format(tender_id))
    auction_bids_data = response.json['data']['bids']
    # posting auction results
    self.app.authorization = ('Basic', ('auction', ''))
    response = self.app.post_json('/tenders/{}/auction'.format(tender_id),
                                  {'data': {'bids': auction_bids_data}})
    # get awards
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
    # get pending award
    award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
    # set award as active
    self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active", "qualified": True, "eligible": True}})
    # lost contract
    tender = self.db.get(tender_id)
    tender['contracts'] = None
    self.db.save(tender)
    # check tender
    response = self.app.get('/tenders/{}'.format(tender_id))
    self.assertEqual(response.json['data']['status'], 'active.awarded')
    self.assertNotIn('contracts', response.json['data'])
    self.assertIn('next_check', response.json['data'])
    # create lost contract
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
    self.assertEqual(response.json['data']['status'], 'active.awarded')
    self.assertIn('contracts', response.json['data'])
    self.assertNotIn('next_check', response.json['data'])
    contract_id = response.json['data']['contracts'][-1]['id']
    # time travel
    tender = self.db.get(tender_id)
    for i in tender.get('awards', []):
        i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
    self.db.save(tender)
    # sign contract
    self.app.authorization = ('Basic', ('broker', ''))
    self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
    # check status
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}'.format(tender_id))
    self.assertEqual(response.json['data']['status'], 'complete')