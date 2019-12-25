#!/usr/bin/env python3


def kernel_parse(path='/proc/cmdline') -> dict:

    kernelcmdline = open(path).read().strip()
    kernel_dict = {}

    for elem in kernelcmdline.split(' '):

        if elem.find('=') != -1:
            elem_parts = elem.split('=')
            kernel_dict.update({elem_parts[0]: elem_parts[1]})
        else:
            kernel_dict.update({elem: elem})

    return kernel_dict


if __name__ == "__main__":
    print(kernel_parse())
