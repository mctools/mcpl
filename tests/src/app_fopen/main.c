#include <stdio.h>
//#  include <unistd.h>
//#  include <limits.h>
//#  include <errno.h>
//#  include <sys/stat.h>

int main(int argc, char** argv)
{
  (void)argc;
  (void)argv;
  {
    printf("Calling fopen wb\n");
    FILE * fh = fopen( "bla.txt","wb");
    if (!fh)
      return 1;
    char data[5] = { 'h','e','l','l','o' };
    printf("Writing data\n");
    if ( fwrite(data, 1, sizeof(data), fh) != sizeof(data) )
      return 1;
    printf("Calling fflush\n");
    fflush(fh);
    printf("Calling fclose\n");
    fclose(fh);
  }
  return 0;
  //Time to modify:
  {
    printf("Calling fopen r+b\n");
    FILE * fh = fopen( "bla.txt","r+b");
    if (!fh)
      return 1;
    printf("Calling fseek 3\n");
#ifdef _WIN32
    int notok = _fseeki64(fh,(__int64)(3), SEEK_SET);
#else
    int notok =  fseek(fh,(ssize_t)(3), SEEK_SET);
#endif
    if (notok)
      return 1;

    char data[4] = { 'y','i','h','a' };
    printf("Writing data\n");
    if ( fwrite(data, 1, sizeof(data), fh) != sizeof(data) )
      return 1;
    printf("Calling fflush\n");
    fflush(fh);
    printf("Calling fclose\n");
    fclose(fh);
  }

  return 0;
}
