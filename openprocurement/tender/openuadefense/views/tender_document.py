# -*- coding: utf-8 -*-
from openprocurement.api.utils import get_now
from openprocurement.tender.core.utils import (
    optendersresource, calculate_business_date
)
from openprocurement.api.validation import ViewPermissionValidationError
from openprocurement.tender.core.validation import validate_operation_with_tender_document_in_not_allowed_status
from openprocurement.tender.openua.views.tender_document import TenderUaDocumentResource as TenderDocumentResource
from openprocurement.tender.openuadefense.constants import TENDERING_EXTRA_PERIOD
from openprocurement.tender.openuadefense.validation import validate_tender_period_extension_with_working_days_in_active_tendering



@optendersresource(name='aboveThresholdUA.defense:Tender Documents',
                   collection_path='/tenders/{tender_id}/documents',
                   path='/tenders/{tender_id}/documents/{document_id}',
                   procurementMethodType='aboveThresholdUA.defense',
                   description="Tender UA.defense related binary files (PDFs, etc.)")
class TenderUaDocumentResource(TenderDocumentResource):

    def validate_update_tender(self, operation):
        try:
            validate_operation_with_tender_document_in_not_allowed_status(self.request, operation)
            validate_tender_period_extension_with_working_days_in_active_tendering(self.request, TENDERING_EXTRA_PERIOD)
        except ViewPermissionValidationError:
            return
        else:
            return True
