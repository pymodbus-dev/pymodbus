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

unsigned char stdin_lrc()
{
    char count = 0;
    int c;

    while ((c = fgetc(stdin)) != EOF) {
        count += c;
    }

    return (unsigned char)(-count);
}

int main(int argc, char **argv)
{
    if (argc == 1) {
      printf("stdin [0x%x]\n", stdin_lrc());
    } else {
      char *data = (char *)argv[1];
      printf("%s [0x%x]\n", data, lrc(data));
    }

    return 0;
}
