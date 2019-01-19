"""
    pimpmyproperty.mixins
    ~~~~~~~~~~~~~~~~~~~~~

    Mixins classes providing extra functionality to classes with pimped properties and methods

    - StorageMixin: Provides an instance based storage.
    - BaseLogMixin: Provides generic log methods.
    - LogMixin: Provides log methods using python logging module.
    - LockMixin: Provides an instance re-entrant lock.
    - AsyncMixin: Provides async capabilities via a queue.
    - CacheMixin: Provides a cache that can be accessed and invalidated.
    - ObservableMixin: Provides signals.

    :copyright: 2019 by pimpmyclass Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from concurrent import futures
import logging
import threading

from . import helpers


class StorageMixin:
    """Mixin class to be inherited by a class that uses a StorageProperty.

    Provides an instance specific storage space divided into namespaces.
    """

    # Instance specific storage, initialized upon first use.
    __storage = None


    @property
    def storage(self):
        """Storage for the instance.

        Returns
        -------
        dict-like object
        """
        if self.__storage is None:
            self.__storage = dict()

        return self.__storage


class BaseLogMixin:
    """Base Mixin class to be inherited by a class requiring logging.

    Derived classes can specify the logger_name by overriding the logger name variable.

    Optionally, an instance of logging.Logger can be attached after instantiation
    using the logger attribute.

    Extra information to each log record can be added permanently using the
    logger extra attribute.
    """

    def log(self, level, msg, *args, **kwargs):
        """Log with the integer severity 'level'
        on the logger corresponding to this class.

        Must be implemented by classes actually logging something.

        Parameters
        ----------
        level :
            severity level for this event.
        msg :
            message to be logged (can contain PEP3101 formatting codes)
        *args :
            arguments passed to logger.log
        **kwargs :
            keyword arguments passed to the logger.log

        See Also
        --------
        log_info, log_debug, log_error, log_warning, log_critical
        """

    def log_info(self, msg, *args, **kwargs):
        """Log with the severity 'INFO' on the logger corresponding to this instance.

        See Also
        --------
        log, log_debug, log_error, log_warning, log_critical
        """
        self.log(logging.INFO, msg, *args, **kwargs)

    def log_debug(self, msg, *args, **kwargs):
        """Log with the severity 'DEBUG' on the logger corresponding to this instance.

        See Also
        --------
        log, log_info, log_error, log_warning, log_critical
        """

        self.log(logging.DEBUG, msg, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        """Log with the severity 'ERROR' on the logger corresponding to this instance.

        See Also
        --------
        log, log_info, log_debug, log_warning, log_critical
        """

        self.log(logging.ERROR, msg, *args, **kwargs)

    def log_warning(self, msg, *args, **kwargs):
        """Log with the severity 'WARNING' on the logger corresponding to this instance.

        See Also
        --------
        log, log_info, log_debug, log_error, log_critical
        """

        self.log(logging.WARNING, msg, *args, **kwargs)

    def log_critical(self, msg, *args, **kwargs):
        """Log with the severity 'CRITICAL' on the logger corresponding to this instance.

        See Also
        --------
        log, log_info, log_debug, log_error, log_warning
        """

        self.log(logging.CRITICAL, msg, *args, **kwargs)


class LogMixin(BaseLogMixin):
    """Mixin class to be inherited by a class requiring logging to Python std logging.

    Derived classes can specify the logger_name by overriding the logger name variable.

    Optionally, an instance of logging.Logger can be attached after instantiation
    using the logger attribute.

    Extra information to each log record can be added permanently using the
    logger extra attribute.
    """

    __logger = None
    __logger_extra = None

    _get_logger = logging.getLogger

    logger_name = None

    @property
    def logger(self):
        if self.__logger is None:
            self.__logger = self.__class__._get_logger(self.logger_name)

        return self.__logger

    @logger.setter
    def logger(self, logger_instance):
        self.__logger = logger_instance

    @property
    def logger_extra(self):
        return self.__logger_extra

    @logger_extra.setter
    def logger_extra(self, dictlike):
        self.__logger_extra = dictlike

    def log(self, level, msg, *args, **kwargs):
        """Log with the integer severity 'level'
        on the logger corresponding to this class.

        Parameters
        ----------
        level :
            severity level for this event.
        msg :
            message to be logged (can contain PEP3101 formatting codes)
        *args :
            arguments passed to logger.log
        **kwargs :
            keyword arguments passed to the logger.log

        See Also
        --------
        log_info, log_debug, log_error, log_warning, log_critical
        """
        if self.__logger_extra:
            self.logger.log(level, msg, *args,
                            extra=dict(self.__logger_extra, **kwargs))
        else:
            self.logger.log(level, msg, *args, **kwargs)


class LockMixin:
    """Mixin class to be inherited by a class requiring a reentrant lock.
    """

    __async_lock = None

    @property
    def lock(self):
        if self.__async_lock is None:
            self.__async_lock = threading.RLock()

        return self.__async_lock


class AsyncMixin(LockMixin):
    """Mixin class to be inherited by a class requiring async operations.

    Async operations are implemented using a single worker Thread Pool Executor
    that returns futures.

    The number of pending tasks can be found in `async_pending`.
    """

    __async_executor = None
    __async_pending = 0

    async_pending = property(lambda self: self.__async_pending)

    @property
    def async_executor(self):
        if self.__async_executor is None:
            self.__async_executor = futures.ThreadPoolExecutor(max_workers=1)

        return self.__async_executor

    def _async_done(self, fut):
        with self.lock:
            self.__async_pending -= 1
        return fut

    def _async_submit(self, fn, *args, **kwargs):
        with self.lock:
            self.__async_pending += 1
        fut = self.async_executor.submit(fn, *args, **kwargs)
        fut.add_done_callback(self._async_done)
        return fut

    def _async_submit_by_name(self, fname, *args, **kwargs):
        return self._async_submit(getattr(self, fname), *args, **kwargs)

    @classmethod
    def attach_async(cls, func):
        def async_func(self, *args, **kwargs):
            return self._async_submit_by_name(func.name, *args, **kwargs)

        async_func = async_func
        async_func.__doc__ = helpers.prepend_to_docstring('(Async) ', func.__doc__)
        setattr(cls, func.name + '_async', async_func)
        return async_func


class CacheMixin:

    _cache_unset_value = None

    def recall(self, keys):
        """Return the last value seen for a CacheProperty or a collection of CacheProperties.

        Parameters
        ----------
        keys : str or iterable of str, optional
            Name of the CacheProperty or properties to recall.

        Returns
        -------
        value of the CacheProperty or dict mapping CacheProperty to values.

        """

        if isinstance(keys, (list, tuple, set)):
            return {key: getattr(self.__class__, key).recall(self) for key in keys}
        return getattr(self.__class__, keys).recall(self)


class ObservableMixin:

    _observer_signal_init = None


