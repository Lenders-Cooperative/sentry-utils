from sentry_sdk.transport import HttpTransport
from environ import Env
import sentry_sdk

class TrafficSplittingHttpTransport(HttpTransport):
    def __init__(self, options, transactions_dsn: str = None, env: Env = None):
        super(TrafficSplittingHttpTransport, self).__init__(options)

        perf_dsn_env_var = 'SENTRY_PERFORMANCE_DSN'
        prod_dsn_env_var = 'SENTRY_DSN'
        if not transactions_dsn:
            if env:
                if env(perf_dsn_env_var, default=None):
                    transactions_dsn = env(perf_dsn_env_var)
                elif env(prod_dsn_env_var, default=None):
                    transactions_dsn = env(prod_dsn_env_var)
                else:
                    message = 'Error during TrafficSplittingHttpTransport __init__. Parameter "transactions_dsn" is undefined and ' \
                              f'environment variables "{prod_dsn_env_var}" and "{prod_dsn_env_var}" are both undefined.'
                    raise RuntimeError(message)
            else:
                message = 'Error during TrafficSplittingHttpTransport __init__. Parameters "transactions_dsn" and "env" are both undefined.'
                raise RuntimeError(message)
        self._transactions_client = sentry_sdk.Client(transactions_dsn)

    def capture_envelope(self, envelope):
        # Do not call super() here to effectively split all transactions into
        # _transactions_client instead of the main client.
        #
        # Note: This assumes transactions are sent as envelopes exclusively
        # (requires sentry_sdk>=0.16)
        #
        # It also assumes that Release Health data (sessions) should end up in
        # TRANSACTIONS_DSN
        event = envelope.get_event()
        if event and event.get("type") == "error":
            return HttpTransport.capture_envelope(self, envelope)
        else:
            return self._transactions_client.transport.capture_envelope(envelope)

    def flush(self, *args, **kwargs):
        self._transactions_client.transport.flush(*args, **kwargs)
        HttpTransport.flush(self, *args, **kwargs)

    def kill(self, *args, **kwargs):
        self._transactions_client.transport.kill(*args, **kwargs)
        HttpTransport.kill(self, *args, **kwargs)