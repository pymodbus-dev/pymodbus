from pymodbus.compat import IS_PYTHON3
if IS_PYTHON3:
    import functools


    def _yielded_return(return_value, *args):
        """Generator factory function with return value."""

        def _():
            """Actual generator producing value."""
            yield
            return return_value

        # return new generator each time this function is called:
        return _()


    def return_as_coroutine(return_value=None):
        """Creates a function that behaves like an asyncio coroutine and returns the given value.

        Typically used as a side effect of a mocked coroutine like this:

            # in module mymod:
            @asyncio.coroutine
            def my_coro_under_test():
                yield from asyncio.sleep(1)
                yield from asyncio.sleep(2)
                return 42

            # in test module:
            @mock.patch('mymod.asyncio.sleep')
            def test_it(mock_sleep):
                mock_sleep.side_effect = return_as_coroutine()
                result = run_coroutine(my_coro_under_test)
                assert mock_sleep.call_count == 2
                assert mock_sleep.call_args_list == [mock.call(1), mock.call(2)]
                assert result == 42
        """
        return functools.partial(_yielded_return, return_value)


    def run_coroutine(coro):
        """Runs a coroutine as top-level task by iterating through all yielded steps."""

        result = None
        try:
            # step through all parts of coro without scheduling anything else:
            while True:
                result = coro.send(result)
        except StopIteration as ex:
            # coro reached end pass on its return value:
            return ex.value
        except:
            raise
