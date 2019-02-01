import mlprocessors as mlpr
import time

class test_processor(mlpr.Processor):
    """
        A test processor
    """
    NAME='test.test_processor'
    VERSION='0.1.1'

    input_file = mlpr.Input('Path of test input file')
    output_file = mlpr.Output('Test output file')
    param1 = mlpr.IntegerParameter('Test integer parameter')
    param2 = mlpr.IntegerParameter('Test integer parameter')

    def run(self):
        print('Sleeping for {} seconds.'.format(self.param1))
        time.sleep(self.param1)
        with open(self.input_file,'r') as f:
            str=f.read()
        str="param1={}, param2={}\n{}".format(self.param1,self.param2,str)
        print(str)
        with open(self.output_file,'w') as f:
            f.write(str)
        return True
    
class test_batch(mlpr.Processor):
    NAME='test_batch'
    VERSION='0.1'

    input_file = mlpr.Input('Path of test input file')
    output_file = mlpr.Output('Test output file')
    param1 = mlpr.IntegerParameter('Test integer parameter')

    def run(self):
        with open(self.input_file,'r') as f:
            str=f.read()
        str="param1={}\n{}".format(self.param1,str)
        print(str)
        with open(self.output_file,'w') as f:
            f.write(str)
        return True