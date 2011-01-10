/**
 * Implementation of the modbus lrc computation
 * :source: The fieldtalk serial implementation guide
 */
#include <stdio.h>
#include <string.h>

unsigned char lrc(const char* data)
{
    char count = 0;
    int i = 0, length = strlen(data);

    for (; i < length; ++i) {
        count += *data++;
    }

    return (unsigned char)(-count);
}

int main(int arc, char **argv)
{
    char *data = (char *)argv[1];
    printf("%s [0%x]", data, lrc(data));

    return 0;
}
