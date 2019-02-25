#!/usr/bin/env python

import json

import os
import traceback
import argparse
from .execute import execute
import types


class ProcessorRegistry:
    def __init__(self, processors=[], namespace=None):
        self.processors = processors
        self.namespace = namespace
        if namespace:
            for proc in self.processors:
                proc.NAME = "{}.{}".format(namespace, proc.NAME)
                proc.NAMESPACE = namespace

    def spec(self):
        s = {}
        s['processors'] = [cls.spec() for cls in self.processors]
        return s

    def find(self, **kwargs):
        for P in self.processors:
            for key in kwargs:
                if not hasattr(P, key):
                    continue
                if getattr(P, key) != kwargs[key]:
                    continue
                return P

    def get_processor_by_name(self, name):
        return self.find(NAME=name)

    def test(self, args, **kwargs):
        procname = args[0]
        proc = self.find(NAME=procname)
        if not proc:
            raise KeyError("Unable to find processor %s" % procname)
        if not hasattr(proc, 'test') or not callable(proc.test):
            raise AttributeError("No test function defined for %s" % proc.NAME)
        print("----------------------------------------------")
        print("Testing", proc.NAME)
        try:
            result = proc.test()
            print("SUCCESS" if result else "FAILURE")
        except Exception as e:
            print("FAILURE:", e)
            if kwargs.get('trace', False):
                traceback.print_exc()
        finally:
            print("----------------------------------------------")

    def process(self, args):
        parser = argparse.ArgumentParser(prog=args[0])
        subparsers = parser.add_subparsers(dest='command', help='main help')
        parser_spec = subparsers.add_parser(
            'spec', help='Print processor specs')
        parser_spec.add_argument('processor', nargs='?')

        parser_test = subparsers.add_parser('test', help='Run processor tests')
        parser_test.add_argument('processor')
        parser_test.add_argument('args', nargs=argparse.REMAINDER)

        for proc in self.processors:
            proc.invoke_parser(subparsers)

        opts = parser.parse_args(args[1:])

        opcode = opts.command
        if not opcode:
            parser.print_usage()
            return
        if opcode == 'spec':
            if opts.processor:
                try:
                    proc = self.get_processor_by_name(opts.processor)
                    print(json.dumps(proc.spec(), sort_keys=True, indent=4))
                except:
                    print("Processor {} not found".format(opts.processor))
                return
            print(json.dumps(self.spec(), sort_keys=True, indent=4))
            return
        if opcode == 'test':
            try:
                self.test([opts.processor]+opts.args, trace=os.getenv('TRACEBACK',
                                                                      False) not in ['0', 0, 'False', 'F', False])
            except KeyError as e:
                # taking __str__ from Base to prevent adding quotes to KeyError
                print(BaseException.__str__(e))
            except Exception as e:
                print(e)
            finally:
                return
        if opcode in [x.NAME for x in self.processors]:
            try:
                self.invoke(self.get_processor_by_name(opcode), args[2:])
            except:
                import sys
                sys.exit(-1)
        else:
            print("Processor {} not found".format(opcode))

    def invoke(self, proc, args):
        return proc.invoke(args)

    def register(self, proc):
        if self.namespace and not proc.NAMESPACE:
            proc.NAME = "{}.{}".format(self.namespace, proc.NAME)
            proc.NAMESPACE = self.namespace
        self.processors.append(proc)


def register_processor(registry):
    def decor(cls):
        cls = mlprocessor(cls)
        registry.register(cls)
        return cls
    return decor


def mlprocessor(cls):
    cls.execute = types.MethodType(execute, cls)
    return cls


registry = ProcessorRegistry()
