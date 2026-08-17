import pytest

from zeta_cli.api.retry import RetryPolicy


def test_default_policy():
    policy = RetryPolicy()

    assert policy.max_attempts == 5
    assert policy.base_delay == 1.0
    assert policy.max_delay == 60.0


def test_exponential_backoff_without_jitter():
    policy = RetryPolicy(
        base_delay=1.0,
        max_delay=100.0,
        jitter=0,
    )

    assert policy.delay_for(0) == 1.0
    assert policy.delay_for(1) == 2.0
    assert policy.delay_for(2) == 4.0
    assert policy.delay_for(3) == 8.0


def test_backoff_is_bounded():
    policy = RetryPolicy(
        base_delay=2.0,
        max_delay=10.0,
        jitter=0,
    )

    assert policy.delay_for(10) == 10.0


def test_retry_limit():
    policy = RetryPolicy(max_attempts=3)

    assert policy.should_retry(0)
    assert policy.should_retry(1)
    assert not policy.should_retry(2)
    assert not policy.should_retry(3)


def test_invalid_policy():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)

    with pytest.raises(ValueError):
        RetryPolicy(base_delay=-1)

    with pytest.raises(ValueError):
        RetryPolicy(base_delay=10, max_delay=5)

    with pytest.raises(ValueError):
        RetryPolicy(jitter=-1)


def test_invalid_attempt():
    policy = RetryPolicy()

    with pytest.raises(ValueError):
        policy.delay_for(-1)
