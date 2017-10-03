import unittest
from openprocurement.tender.core.tests.configurator import ConfiguratorTestMixin
from openprocurement.tender.openuadefense.adapters import TenderAboveThresholdUADefConfigurator
from openprocurement.tender.openuadefense.models import Tender


class ConfiguratorTest(unittest.TestCase, ConfiguratorTestMixin):
    configurator_class = TenderAboveThresholdUADefConfigurator
    reverse_awarding_criteria = False
    awarding_criteria_key = 'not yet implemented'
    configurator_model = Tender


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ConfiguratorTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
