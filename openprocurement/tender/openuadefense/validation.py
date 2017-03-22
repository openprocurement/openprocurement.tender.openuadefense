# -*- coding: utf-8 -*-
from openprocurement.api.validation import ViewPermissionValidationError
from openprocurement.api.utils import get_now
from openprocurement.tender.core.utils import calculate_business_date

def validate_tender_period_extension_with_working_days(request, tender, TENDERING_EXTRA_PERIOD):
    if calculate_business_date(get_now(), TENDERING_EXTRA_PERIOD, tender, True) > request.validated['tender'].tenderPeriod.endDate:
        request.errors.add('body', 'data', 'tenderPeriod should be extended by {0.days} working days'.format(TENDERING_EXTRA_PERIOD))
        request.errors.status = 403
        raise ViewPermissionValidationError


def validate_tender_period_extension_with_working_days_in_active_tendering(request, TENDERING_EXTRA_PERIOD):
    if request.validated['tender_status'] == 'active.tendering' and calculate_business_date(get_now(), TENDERING_EXTRA_PERIOD, request.validated['tender'], True) > request.validated['tender'].tenderPeriod.endDate:
        request.errors.add('body', 'data', 'tenderPeriod should be extended by {0.days} working days'.format(TENDERING_EXTRA_PERIOD))
        request.errors.status = 403
        raise ViewPermissionValidationError
