import mlprocessors as mlpr

class TestProcessor(mlpr.Processor):
    NAME='TestProcessor'
    VERSION='0.1.0'
    
    input_file=mlpr.Input('The input file')
    output_file1=mlpr.Output('The output file')
    output_file2=mlpr.Output('The second output file')
    
    param1=mlpr.StringParameter('A string')
    
    def run(self):
        print('Running TestProcessor...')
        with open(self.input_file) as f:
          txt=f.read()
        txt=txt+'---- '+self.param1
        with open(self.output_file1,'w') as f:
          f.write(txt)
        txt=txt+'---- '+self.param1
        with open(self.output_file2,'w') as f:
          f.write(txt)