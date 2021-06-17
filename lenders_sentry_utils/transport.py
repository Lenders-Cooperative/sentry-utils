from sentry_sdk.transport import HttpTransport

class TrafficSplittingHttpTransport(HttpTransport):
    _transactions_client = None

    def capture_envelope(self, envelope):
        # Do not call super() here to effectively split all transactions into
        # _transactions_client instead of the main client.
        #
        # Note: This assumes transactions are sent as envelopes exclusively
        # (requires sentry_sdk>=0.16)
        #
        # It also assumes that Release Health data (sessions) should end up in
        # TRANSACTIONS_DSN
        self.confirm_client()
        event = envelope.get_event()
        if event and event.get("type") == "error":
            return HttpTransport.capture_envelope(self, envelope)
        else:
            return self._transactions_client.transport.capture_envelope(envelope)

    def flush(self, *args, **kwargs):
        self.confirm_client()
        self._transactions_client.transport.flush(*args, **kwargs)
        HttpTransport.flush(self, *args, **kwargs)

    def kill(self, *args, **kwargs):
        self.confirm_client()
        self._transactions_client.transport.kill(*args, **kwargs)
        HttpTransport.kill(self, *args, **kwargs)

    def confirm_client(self):
        if not self._transactions_client:
            message = "The transaction splitting transport class was not initialized. Ensure the function 'traffic_splitting_http_transport_init' was executed."
            raise EnvironmentError(message)