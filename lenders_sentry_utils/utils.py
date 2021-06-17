from typing import List

import environ
from environ import Env
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from .transport import TrafficSplittingHttpTransport

def _traffic_splitting_http_transport_init(env: Env):
    transactions_dsn = env('SENTRY_TRANSACTIONS_DSN', default=None)
    TrafficSplittingHttpTransport._transactions_client = sentry_sdk.Client(transactions_dsn)

def _get_var_from_env(env: Env, env_var_name: str, var_name: str):
    message_start = f'\nSentry configured incorrectly. "{var_name}" was not passed to sentry_init and '
    if not env:
        message = message_start + f'an env was not passed to search for {env_var_name}.'
        raise EnvironmentError(message)
    try:
        return env(env_var_name)
    except environ.ImproperlyConfigured:
        message = message_start + f'{env_var_name} was not set in env.'
        raise EnvironmentError(message)
    except:
        message = message_start + f'an unknown error occurred when attempting to read environment variable {env_var_name}.'
        raise RuntimeError(message)

def sentry_init(env: Env = None,
                dsn: str = None,
                transport = None,
                traces_sample_rate: float = 0.1,
                debug: bool = False,
                integrations: List = None,
                send_default_pii: bool = True,
                environment: str = None,
                before_send = None,
                release: str = None):
    dsn_env_var = "SENTRY_DSN"
    environment_env_var = "BASE_URL"
    release_env_var = "VERSION"
    dsn = dsn or _get_var_from_env(env, dsn_env_var, "dsn")
    environment = environment or _get_var_from_env(env, environment_env_var, "environment")
    release = release or env(release_env_var, default=None)
    integrations = integrations or [DjangoIntegration(),CeleryIntegration(),RedisIntegration()]

    if transport is TrafficSplittingHttpTransport:
        _traffic_splitting_http_transport_init(env)

    sentry_sdk.init(
        dsn,
        transport=transport,
        traces_sample_rate=traces_sample_rate,
        debug=debug,
        integrations=integrations,
        send_default_pii=send_default_pii,
        environment=environment,
        before_send=before_send,
        release=release,
    )

def protect_body(event, hint):
    if 'request' in event and 'data' in event['request']:
        event['request']['orig_data'] = event['request']['data']
    return event

def capture_exception(e):
    """
        Wrapper for sentry_sdk.capture_exception
    """
    with sentry_sdk.configure_scope() as scope:
        scope.add_event_processor(protect_body)
        sentry_sdk.capture_exception(e, scope=scope)