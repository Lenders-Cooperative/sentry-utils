# Lenders Sentry Utils
This is a package containing Sentry related utilities used across several Lenders Cooperative projects.

## Installation

`$ pip install lenders-sentry-utils`

## Usage
There are two major components in the package, `sentry_init` and `TrafficSplittingHttpTransport`.
These are explained in the sections below.
Additionally, there is one minor component, `capture_exception`.
This is a simple wrapper for `sentry_sdk.capture_exception` that adds an event processor to protect a request's body if it exists in the event.

### Sentry Init
This package's `sentry_init` is a wrapper for `sentry_sdk.init` with default values and automatic checking of environment variables.
The following table lists each parameter and its relevant information.
Any parameter with no description directly corresponds to a `sentry_sdk.init` option.

| Parameter name | Type | Default value | Description |
| --- | --- | --- | --- |
| env | Env | None | An Env object to search if `dsn` or `environment` are not passed |
| dsn | str | env("SENTRY_DSN") |  |
| environment | str | env("BASE_URL") |  |
| debug | bool | False |  |
| send_default_pii | bool | True |  |
| traces_sample_rate | float | 0.1 |  |
| integrations | List | Django, Celery, Redis integrations |  |
| transport | Transport | HTTPTransport |  |
| before_send | function | None |  |

Note: `env`, `dsn`, and `environment` are dependent on each other to a certain degree.
If `dsn` or `environment` are not passed as parameters, `env` must be passed in order to pull the corresponding environment variable.
Additionally, if `dsn` or `environment` are passed, the passed value will be used even if the corresponding environment variable exists in `env`.

#### Sentry Init Examples
```python
from lenders_sentry_utils import sentry_init
from environ import Env

env = Env(
    SENTRY_DSN = (str, 'https://PK@sentry.io/0'),
    BASE_URL = (str, 'base.com'),
)

# Minimum viable function call
sentry_init(env=env)

# Forcing a DSN that's not in the environment
different_dsn = 'https://different@not.sentry.io/3'
sentry_init(env=env, dsn=different_dsn)

# Setting DSN and environment without using environment variables
sentry_init(dsn=different_dsn, environment='special.env.com')
```

### TrafficSplittingHttpTransport
`TrafficSplittingHttpTransport` is a custom transport that splits transaction events to a second DSN while still sending error events to the primary DSN. 
This is usually done for billing purposes to ensure that all errors can be reported to Sentry.
To use this transport, the environment variable `SENTRY_TRANSACTIONS_DSN` must be set with the second DSN as its value.
If this environment variable is not set, transaction events will instead be discarded.

Additionally, the function `traffic_splitting_http_transport_init` must be called before an instance of the class is created.
This function is what properly initializes the second DSN to handle transport events.

#### TrafficSplittingHttpTransport Examples
```python
import lenders_sentry_utils as lsu
from environ import Env

base_env = Env(
    SENTRY_DSN = (str, 'https://error_dsn@sentry.io/0'),
    BASE_URL = (str, 'base.com'),
)
send_transactions_env = Env(
    SENTRY_TRANSACTIONS_DSN = (str, 'https://transactions_dsn@sentry.io/0'),
)

# Example 1: Sending transaction events
lsu.traffic_splitting_http_transport_init(send_transactions_env)
lsu.sentry_init(env=base_env, transport=lsu.TrafficSplittingHttpTransport)

# Example 2: Ignoring transaction events
lsu.traffic_splitting_http_transport_init(Env())
lsu.sentry_init(env=base_env, transport=lsu.TrafficSplittingHttpTransport)
```