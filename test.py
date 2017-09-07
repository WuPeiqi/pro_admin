#!/usr/bin/env python
# -*- coding:utf-8 -*-


class Foo(object):

    def __iter__(self):
        yield 1
        yield 2



for i in Foo():
    print(i)
