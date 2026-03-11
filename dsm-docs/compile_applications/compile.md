# Compile Applications Manually

## Overview

This page provides guidance on compiling a C application using the Synology DSM tool chain.

## Example Application

The documentation presents a sample program called `examplePkg.c`:

```c
#include <sys/sysinfo.h>

int main()
{
    struct sysinfo info;
    int ret;
    ret = sysinfo(&info);
    if (ret != 0) {
        printf("Failed to get system information.\n");
        return -1;
    }
    printf("Total RAM: %u\n", info.totalram);
    printf("Free RAM: %u\n", info.freeram);
    return 0;
}
```

This program retrieves and displays system memory information.

## Direct Compilation Command

To compile the application directly:

```
/usr/local/arm-marvell-linux-gnueabi/bin/arm-marvell-linux-gnueabi-gcc examplePkg.c -o sysinfo
```

## Makefile Approach

Alternatively, use a Makefile for automated compilation:

```makefile
EXEC= sysinfo
OBJS= sysinfo.o

CC= /usr/local/arm-marvell-linux-gnueabi/bin/arm-marvell-linux-gnueabi-gcc
LD= /usr/local/arm-marvell-linux-gnueabi/bin/arm-marvell-linux-gnueabi-ld
CFLAGS += -I/usr/local/arm-marvell-linux-gnueabi/arm-marvell-linux-gnueabi/libc/include
LDFLAGS += -L/usr/local/arm-marvell-linux-gnueabi/arm-marvell-linux-gnueabi/libc/lib

all: $(EXEC)

$(EXEC): $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $@ $(LDFLAGS)

clean:
	rm -rf *.o $(PROG) *.core
```
