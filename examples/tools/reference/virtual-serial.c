#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>

int main(int argc, char *argv[])
{
    char *buffer = calloc(256, sizeof(char));

    int pt = open("/dev/ptmx", O_RDWR | O_NOCTTY);
    if (pt < 0) {
        perror("open /dev/ptmx");
        return -1;
    }
    grantpt(pt);
    unlockpt(pt);
    fprintf(stderr, "Slave Device: %s\n", (char *)ptsname(pt));

    while(1) {
        int size = read(pt, buffer, 256);
        if (size > 0) {
            fprintf(stderr, "%s", buffer);
        }
    }
    free(buffer);

    return 0;
}
