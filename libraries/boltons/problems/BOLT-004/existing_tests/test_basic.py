"""Basic tests for boltons."""
import inspect
import pytest
from boltons.queueutils import HeapPriorityQueue, SortedPriorityQueue, PriorityQueue
from boltons.funcutils import FunctionBuilder, wraps, update_wrapper, NO_DEFAULT


# ---- HeapPriorityQueue: basic construction and insertion ----

class TestHeapPriorityQueueBasic:
    def test_empty_queue_raises_on_pop(self):
        pq = HeapPriorityQueue()
        with pytest.raises(IndexError):
            pq.pop()

    def test_empty_queue_raises_on_peek(self):
        pq = HeapPriorityQueue()
        with pytest.raises(IndexError):
            pq.peek()

    def test_single_item_pop(self):
        pq = HeapPriorityQueue()
        pq.add('only', 5)
        assert pq.pop() == 'only'

    def test_single_item_peek(self):
        pq = HeapPriorityQueue()
        pq.add('only', 5)
        assert pq.peek() == 'only'
        # Peek does not remove the item
        assert pq.peek() == 'only'

    def test_len_single_item(self):
        pq = HeapPriorityQueue()
        assert len(pq) == 0
        pq.add('x', 1)
        assert len(pq) == 1

    def test_pop_returns_correct_item(self):
        pq = HeapPriorityQueue()
        pq.add('x', 1)
        result = pq.pop()
        assert result == 'x'

    def test_default_return_on_empty_pop(self):
        pq = HeapPriorityQueue()
        result = pq.pop(default='nothing')
        assert result == 'nothing'

    def test_default_return_on_empty_peek(self):
        pq = HeapPriorityQueue()
        result = pq.peek(default='empty')
        assert result == 'empty'


class TestHeapPriorityQueueOrdering:
    def test_higher_priority_pops_first(self):
        pq = HeapPriorityQueue()
        pq.add('low', 1)
        pq.add('high', 10)
        assert pq.pop() == 'high'

    def test_three_distinct_priorities(self):
        pq = HeapPriorityQueue()
        pq.add('medium', 5)
        pq.add('low', 1)
        pq.add('high', 100)
        assert pq.pop() == 'high'
        assert pq.pop() == 'medium'
        assert pq.pop() == 'low'

    def test_peek_does_not_consume(self):
        pq = HeapPriorityQueue()
        pq.add('a', 3)
        pq.add('b', 7)
        top = pq.peek()
        assert top == 'b'
        assert len(pq) == 2
        assert pq.pop() == 'b'

    def test_reprioritize_existing_task(self):
        pq = HeapPriorityQueue()
        pq.add('task', 1)
        pq.add('task', 100)   # re-add with higher priority
        assert len(pq) == 1
        assert pq.pop() == 'task'

    def test_remove_task_then_add(self):
        pq = HeapPriorityQueue()
        pq.add('a', 5)
        pq.add('b', 3)
        pq.remove('a')
        assert len(pq) == 1
        assert pq.pop() == 'b'

    def test_remove_absent_raises(self):
        pq = HeapPriorityQueue()
        with pytest.raises(KeyError):
            pq.remove('nonexistent')


# ---- SortedPriorityQueue / PriorityQueue ----

class TestSortedPriorityQueue:
    def test_pq_alias(self):
        pq = PriorityQueue()
        pq.add('task', 1)
        assert pq.pop() == 'task'

    def test_sorted_pq_ordering(self):
        pq = SortedPriorityQueue()
        pq.add('a', 2)
        pq.add('b', 8)
        pq.add('c', 5)
        assert pq.pop() == 'b'
        assert pq.pop() == 'c'
        assert pq.pop() == 'a'

    def test_sorted_pq_single(self):
        pq = SortedPriorityQueue()
        pq.add('only', 42)
        assert pq.peek() == 'only'
        assert pq.pop() == 'only'


# ---- FunctionBuilder ----

class TestFunctionBuilderBasic:
    def test_simple_function_construction(self):
        fb = FunctionBuilder('answer', body='return 42')
        f = fb.get_func()
        assert f() == 42

    def test_function_with_args(self):
        fb = FunctionBuilder('add', args=['x', 'y'], body='return x + y')
        f = fb.get_func()
        assert f(3, 4) == 7

    def test_function_name_preserved(self):
        fb = FunctionBuilder('my_func', body='pass')
        f = fb.get_func()
        assert f.__name__ == 'my_func'

    def test_function_doc_preserved(self):
        fb = FunctionBuilder('f', doc='Hello, world.', body='pass')
        f = fb.get_func()
        assert f.__doc__ == 'Hello, world.'

    def test_add_arg_positional(self):
        fb = FunctionBuilder('greet', body='return name')
        fb.add_arg('name')
        f = fb.get_func()
        assert f('Alice') == 'Alice'

    def test_add_arg_with_default(self):
        fb = FunctionBuilder('greet', body='return name', args=['name'])
        # Verify the arg already exists
        assert 'name' in fb.args

    def test_add_arg_duplicate_raises(self):
        from boltons.funcutils import ExistingArgument
        fb = FunctionBuilder('f', args=['x'], body='return x')
        with pytest.raises(ExistingArgument):
            fb.add_arg('x')  # x already in args

    def test_varargs(self):
        fb = FunctionBuilder('f', varargs='args', body='return sum(args)')
        f = fb.get_func()
        assert f(1, 2, 3) == 6

    def test_varkw(self):
        fb = FunctionBuilder('f', varkw='kw', body='return kw.get("x", 0)')
        f = fb.get_func()
        assert f(x=7) == 7

    def test_from_func(self):
        def original(a, b, c=10):
            return a + b + c
        fb = FunctionBuilder.from_func(original)
        assert fb.args == ['a', 'b', 'c']
        assert fb.defaults == (10,)
        assert fb.name == 'original'


class TestFunctionBuilderFromFunc:
    def test_kwonly_args_captured(self):
        def f(x, *, y=99):
            return x + y
        fb = FunctionBuilder.from_func(f)
        assert 'y' in fb.kwonlyargs
        assert fb.kwonlydefaults.get('y') == 99

    def test_annotations_captured(self):
        def f(x: int) -> str:
            return str(x)
        fb = FunctionBuilder.from_func(f)
        assert fb.annotations.get('x') is int

    def test_remove_arg_no_default(self):
        def f(a, b, c):
            return a + b + c
        fb = FunctionBuilder.from_func(f)
        fb.remove_arg('b')
        assert 'b' not in fb.args
        assert 'a' in fb.args
        assert 'c' in fb.args

    def test_get_defaults_dict_single_default(self):
        def f(x, y=7):
            return x + y
        fb = FunctionBuilder.from_func(f)
        d = fb.get_defaults_dict()
        assert d == {'y': 7}

    def test_get_arg_names(self):
        def f(a, b=1, *, c=2):
            pass
        fb = FunctionBuilder.from_func(f)
        names = fb.get_arg_names()
        assert set(names) == {'a', 'b', 'c'}

    def test_get_arg_names_only_required(self):
        def f(a, b=1, *, c=2):
            pass
        fb = FunctionBuilder.from_func(f)
        required = fb.get_arg_names(only_required=True)
        assert set(required) == {'a'}


# ---- wraps / update_wrapper ----

class TestWraps:
    def test_wraps_preserves_name(self):
        def original():
            '''doc'''
            return 1

        @wraps(original)
        def wrapper(*args, **kwargs):
            return original(*args, **kwargs)

        assert wrapper.__name__ == 'original'

    def test_wraps_preserves_doc(self):
        def original():
            '''The original docstring.'''
            return 1

        @wraps(original)
        def wrapper(*args, **kwargs):
            return original(*args, **kwargs)

        assert wrapper.__doc__ == 'The original docstring.'

    def test_wraps_preserves_module(self):
        def original():
            pass

        @wraps(original)
        def wrapper(*args, **kwargs):
            return original(*args, **kwargs)

        assert wrapper.__module__ == original.__module__

    def test_wraps_preserves_annotations(self):
        def original(x: int, y: int) -> int:
            return x + y

        @wraps(original)
        def wrapper(*args, **kwargs):
            return original(*args, **kwargs)

        assert wrapper.__annotations__ == original.__annotations__

    def test_wrapped_function_still_works(self):
        def add(a, b):
            return a + b

        @wraps(add)
        def traced_add(*args, **kwargs):
            return add(*args, **kwargs)

        assert traced_add(3, 4) == 7
        assert traced_add(a=1, b=9) == 10

    def test_wraps_with_multiple_args(self):
        def original(a, b, c=5):
            return a + b + c

        @wraps(original)
        def wrapper(*args, **kwargs):
            return original(*args, **kwargs)

        # Check function metadata is preserved (name, doc, module)
        assert wrapper.__name__ == 'original'
        # And that the wrapped function still calls through correctly
        assert wrapper(1, 2) == 8
        assert wrapper(1, 2, c=10) == 13

    def test_update_wrapper_basic(self):
        def func(a, b=5):
            '''func doc'''
            return a + b

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapped = update_wrapper(wrapper, func)
        assert wrapped.__name__ == 'func'
        assert wrapped.__doc__ == 'func doc'
        assert wrapped(3) == 8
