import copy
import pytest
from core.services.remote_config_service import DEFAULT_REMOTE_CONFIG_DOCUMENT, validate_remote_config_document, RemoteConfigValidationError

def document(value):
    result = copy.deepcopy(DEFAULT_REMOTE_CONFIG_DOCUMENT)
    result['parameters']['telemetry'] = {'default': value, 'rules': []}
    return result

@pytest.mark.parametrize('mode', ['appmetrica', 'off'])
def test_local_modes(mode):
    validate_remote_config_document(document({'mode': mode}))

@pytest.mark.parametrize('mode', ['sentry', 'both'])
def test_trusted_collector(mode):
    validate_remote_config_document(document({'mode': mode, 'sentry_dsn': 'https://public@sentry.roadmapik.com/2'}))

@pytest.mark.parametrize('value', [None, {'mode':'unknown'}, {'mode':'sentry'}, {'mode':'both','sentry_dsn':'https://public@attacker.test/2'}, {'mode':'both','sentry_dsn':'http://public@sentry.roadmapik.com/2'}, {'mode':'both','sentry_dsn':'https://public:secret@sentry.roadmapik.com/2'}, {'mode':'off', 'token':'secret'}])
def test_invalid_policy_rejected(value):
    with pytest.raises(RemoteConfigValidationError):
        validate_remote_config_document(document(value))

def test_rules_are_validated_too():
    result = document({'mode':'appmetrica'})
    result['parameters']['telemetry']['rules'] = [{'id':'bad','conditions': [], 'value':{'mode':'sentry'}}]
    with pytest.raises(RemoteConfigValidationError):
        validate_remote_config_document(result)
