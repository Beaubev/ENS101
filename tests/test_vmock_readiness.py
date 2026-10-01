import unittest

from readiness_client import ReadinessContractError, validate_projection
from test_readiness_client import valid_projection


def vmock_projection():
    payload = valid_projection()
    payload['sources']['vmock'] = {'status': 'fresh', 'imported_at': '2026-10-01T10:20:00+00:00'}
    payload['data']['vmock'] = {
        'signed_up': True, 'resume_uploaded': True, 'resume_upload_count': 2,
        'latest_score': 78, 'latest_zone': 'green',
        'latest_subscores': {'impact': 28, 'presentation': 26, 'competencies': 24},
        'first_score': 80, 'highest_score': 80, 'latest_upload_date': '2026-09-30',
    }
    return payload


class VMockContractTests(unittest.TestCase):
    def test_older_hub_without_optional_vmock_remains_supported(self):
        validate_projection(valid_projection(), http_status=200)

    def test_valid_optional_data_and_stale_source_do_not_change_readiness(self):
        payload = vmock_projection()
        payload['sources']['vmock']['status'] = 'stale'
        validate_projection(payload, http_status=200)
        self.assertEqual(payload['record_status'], 'complete')
        self.assertEqual(payload['freshness'], 'fresh')

    def test_missing_record_and_no_resume(self):
        payload = vmock_projection()
        payload['data']['vmock'] = None
        validate_projection(payload, http_status=200)
        payload = vmock_projection()
        record = payload['data']['vmock']
        record.update(resume_uploaded=False, latest_zone=None, latest_score=None,
                      first_score=None, highest_score=None, latest_upload_date=None,
                      latest_subscores=None)
        validate_projection(payload, http_status=200)

    def test_malformed_optional_data_is_rejected(self):
        mutations = [
            ('latest_zone', 'blue'), ('latest_score', True), ('latest_score', 101),
            ('signed_up', 1), ('resume_upload_count', -1), ('resume_uploaded', False),
            ('latest_upload_date', '09/30/2026'), ('latest_subscores', {'impact': 28}),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                payload = vmock_projection()
                payload['data']['vmock'][key] = value
                with self.assertRaises(ReadinessContractError):
                    validate_projection(payload, http_status=200)
        payload = vmock_projection()
        payload['sources']['vmock']['status'] = 'unknown'
        with self.assertRaises(ReadinessContractError):
            validate_projection(payload, http_status=200)
