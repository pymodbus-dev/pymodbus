#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>

//
// constants
//
#define BUFFER_SIZE 256

int setnonblock(int sock) {
    int flags = fcntl(sock, F_GETFL, 0);
    if (flags == -1) {
        return -1;
    }
    return fcntl(sock, F_SETFL, flags | O_NONBLOCK);
}

//
// main virtual serial runner
//
int main(int argc, char *argv[])
{
    char *buffer = calloc(BUFFER_SIZE, sizeof(char));

    int size = 0;
    int ptcl = open("/dev/ptmx", O_RDWR | O_NOCTTY);
    if (ptcl < 0) {
        perror("open /dev/ptmx");
        return -1;
    }
    grantpt(ptcl);
    unlockpt(ptcl);
    fprintf(stderr, "client device-> %s\n", (char *)ptsname(ptcl));

    int ptma = open("/dev/ptmx", O_RDWR | O_NOCTTY);
    if (ptma < 0) {
        perror("open /dev/ptmx");
        return -1;
    }
    grantpt(ptma);
    unlockpt(ptma);
    fprintf(stderr, "master device-> %s\n", (char *)ptsname(ptma));

    while (1) {
        size = read(ptcl, buffer, BUFFER_SIZE);
        if (size > 0) {
            write(ptma, buffer, size);
            fprintf(stderr, "client-> %s", buffer);
        }

        size = read(ptma, buffer, BUFFER_SIZE);
        if (size > 0) {
            write(ptcl, buffer, size);
            fprintf(stderr, "master-> %s", buffer);
        }
    }
    free(buffer);
    close(ptcl);
    close(ptma);

    return 0;
}
