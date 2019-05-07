import mlprocessors as mlpr
import pytest

_global = dict(
    num_times_directly_called=0
)


class RepeatText(mlpr.Processor):
    textfile = mlpr.Input(help="input text file")
    textfile_out = mlpr.Output(help="output text file")
    num_repeats = mlpr.IntegerListParameter(help="Number of times to repeat the text")

    def run(self):
        _global['num_times_directly_called'] = _global['num_times_directly_called'] + 1
        assert self.num_repeats >= 0
        with open(self.textfile, 'r') as f:
            txt = f.read()
        txt2 = ''
        for _ in range(self.num_repeats):
            txt2 = txt2 + txt
        with open(self.textfile_out, 'w') as f:
            f.write(txt2)


@pytest.mark.test_skip_failing
def test_skip_failing():
    with open('tmp.txt', 'w') as f:
        f.write('some text to repeat\n')
    a = _global['num_times_directly_called']

    print('test_skip_failing part 1')
    r = RepeatText.execute(textfile='tmp.txt', textfile_out='tmp2.txt', num_repeats=3, _force_run=True)
    assert r.retcode == 0
    b = _global['num_times_directly_called']
    assert b - a == 1

    print('test_skip_failing part 2')
    r = RepeatText.execute(textfile='tmp.txt', textfile_out='tmp3.txt', num_repeats=3)
    assert r.retcode == 0
    b = _global['num_times_directly_called']
    assert b - a == 1

    print('test_skip_failing part 3')
    r = RepeatText.execute(textfile='tmp.txt', textfile_out='tmp4.txt', num_repeats=-3, _force_run=True)
    assert r.retcode != 0
    b = _global['num_times_directly_called']
    assert b - a == 2

    print('test_skip_failing part 4')
    r = RepeatText.execute(textfile='tmp.txt', textfile_out='tmp5.txt', num_repeats=-3)
    assert r.retcode != 0
    b = _global['num_times_directly_called']
    assert b - a == 3

    print('test_skip_failing part 5')
    r = RepeatText.execute(textfile='tmp.txt', textfile_out='tmp6.txt', num_repeats=-3, _skip_failing=True)
    assert r.retcode != 0
    b = _global['num_times_directly_called']
    assert b - a == 3
