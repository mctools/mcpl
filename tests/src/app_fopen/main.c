
////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  This file is part of MCPL (see https://mctools.github.io/mcpl/)           //
//                                                                            //
//  Copyright 2015-2025 MCPL developers.                                      //
//                                                                            //
//  Licensed under the Apache License, Version 2.0 (the "License");           //
//  you may not use this file except in compliance with the License.          //
//  You may obtain a copy of the License at                                   //
//                                                                            //
//      http://www.apache.org/licenses/LICENSE-2.0                            //
//                                                                            //
//  Unless required by applicable law or agreed to in writing, software       //
//  distributed under the License is distributed on an "AS IS" BASIS,         //
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  //
//  See the License for the specific language governing permissions and       //
//  limitations under the License.                                            //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <stdio.h>

#ifdef _MSC_VER
#  pragma warning( push )
#  pragma warning( disable : 4996 )
#endif
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
#ifdef _MSC_VER
#  pragma warning( pop )
#endif
