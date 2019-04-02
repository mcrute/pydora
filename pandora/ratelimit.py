"""
Pandora Rate Limiter
"""
import time
import warnings

from .errors import PandoraException


class RateLimitExceeded(PandoraException):
    """Exception thrown when rate limit is exceeded
    """

    code = 0
    message = "Rate Limit Exceeded"


class TokenBucketCallbacks(object):
    """Interface for TokenBucket Callbacks

    These methods get called by the token bucket during certain parts of the
    bucket lifecycle.
    """

    def near_depletion(self, tokens_left):
        """Bucket near depletion callback

        This callback is called when the token bucket is nearly depleted, as
        defined by the depletion_level member of the TokenBucket class. This
        method provides a hook for clients to warn when the token bucket is
        nearly consumed. The return value of this method is ignored.
        """
        return

    def depleted(self, tokens_wanted, tokens_left):
        """Bucket depletion callback

        This callback is called when the token bucket has been depleted.
        Returns a boolean indicating if the bucket should call its default
        depletion handler. If this method returns False the token bucket will
        not return any tokens but will also not call the default token
        depletion handler.

        This method is useful if clients want to customize depletion behavior.
        """
        return True

    def consumed(self, tokens_wanted, tokens_left):
        """Bucket consumption callback

        This callback is called when a client successfully consumes tokens from
        a bucket. The return value of this method is ignored.
        """
        return


class TokenBucket(object):
    def __init__(self, capacity, refill_tokens, refill_rate, callbacks=None):
        """Initialize a rate limiter

        capacity
            the number of tokens the bucket holds when completely full
        refill_tokens
            number of tokens to add to the bucket during each refill cycle
        refill_rate
            the number of seconds between token refills
        """
        self.capacity = capacity
        self.refill_tokens = refill_tokens
        self.refill_rate = refill_rate
        self.callbacks = callbacks or TokenBucketCallbacks()

        # Depletion level at which the near_depletion callback is called.
        # Defaults to 20% of the bucket available. Not exposed in the
        # initializer because this should generally be good enough.
        self.depletion_level = self.capacity / 5

        self._available_tokens = capacity
        self._last_refill = time.time()

    @classmethod
    def creator(cls, callbacks=None):
        """Returns a TokenBucket creator

        This method is used when clients want to customize the callbacks but
        defer class construction to the real consumer.
        """

        def constructor(capacity, refill_tokens, refill_rate):
            return cls(capacity, refill_tokens, refill_rate, callbacks)

        return constructor

    def _replentish(self):
        now = time.time()

        refill_unit = round((now - self._last_refill) / self.refill_rate)
        if refill_unit > 0:
            self._last_refill = now
            self._available_tokens = min(
                self.capacity, refill_unit * self.refill_tokens
            )

    def _insufficient_tokens(self, tokens_wanted):
        return

    def _sufficient_tokens(self, tokens_wanted):
        return

    def consume(self, tokens=1):
        """Consume a number of tokens from the bucket

        May return a boolean indicating that sufficient tokens were available
        for consumption. Implementations may have different behaviour when the
        bucket is empty. This method may block or throw.
        """
        self._replentish()

        if self._available_tokens >= tokens:
            self._available_tokens -= tokens

            if self._available_tokens <= self.depletion_level:
                self.callbacks.near_depletion(self._available_tokens)

            self.callbacks.consumed(tokens, self._available_tokens)
            self._sufficient_tokens(tokens)

            return True
        else:
            if self.callbacks.depleted(tokens, self._available_tokens):
                self._insufficient_tokens(tokens)
            return False


class BlockingTokenBucket(TokenBucket):
    """Token bucket that blocks on exhaustion
    """

    def _insufficient_tokens(self, tokens_wanted):
        tokens_per_second = self.refill_rate / self.refill_tokens
        excess_tokens = tokens_wanted - self._available_tokens
        time.sleep(tokens_per_second * excess_tokens)


class ThrowingTokenBucket(TokenBucket):
    """Token bucket that throws on exhaustion
    """

    def _insufficient_tokens(self, tokens_wanted):
        raise RateLimitExceeded("Unable to acquire enough tokens")


class WarningTokenBucket(TokenBucket):
    """Token bucket that warns on exhaustion

    This token bucket doesn't enforce the rate limit and is designed to be a
    softer policy for backwards compatability with code that was written before
    rate limiting was added.
    """

    def _insufficient_tokens(self, tokens_wanted):
        warnings.warn(
            "Pandora API rate limit exceeded!", warnings.ResourceWarning
        )
