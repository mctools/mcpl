
////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  This file is part of MCPL (see https://mctools.github.io/mcpl/)           //
//                                                                            //
//  Copyright 2015-2026 MCPL developers.                                      //
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

//Numbers in stat:sum: values, and in the text files of mcpltool --text, always
//use "." as the decimal point, also when the application uses a locale with
//another decimal point (like ","). The test is done with the first such locale
//available (there might be none, but the output is the same either way):

#include "mcpl.h"
#include "mcpltest_errstate.h"
#include <locale.h>
#include <stdio.h>
#include <string.h>

static int set_comma_locale(void)
{
  const char * names[] = { "de_DE.UTF-8", "de_DE.utf8", "de_DE",
                           "fr_FR.UTF-8", "fr_FR.utf8", "fr_FR",
                           "da_DK.UTF-8", "German_Germany.1252", "de-DE" };
  for ( size_t i = 0; i < sizeof(names)/sizeof(names[0]); ++i ) {
    if ( names[i] && setlocale( LC_NUMERIC, names[i] )
         && strcmp( localeconv()->decimal_point, "." ) != 0 )
      return 1;
  }
  setlocale( LC_NUMERIC, "C" );
  return 0;
}

int main(void)
{
  (void)set_comma_locale();
  const double values[] = { 1234.5, 0.1, 1e-300, 2.5e10, 123456789.123,
                            -1.0, 0.0 };
  const unsigned nvalues = sizeof(values)/sizeof(values[0]);
  mcpl_outfile_t f = mcpl_create_outfile("statsumlocale.mcpl");
  for ( unsigned i = 0; i < nvalues; ++i ) {
    char key[16];
    snprintf(key,sizeof(key),"v%u",i);
    mcpl_hdr_add_stat_sum(f,key,values[i]);
  }
  mcpl_close_outfile(f);

  mcpl_file_t fi = mcpl_open_file("statsumlocale.mcpl");
  int ok = 1;
  for ( unsigned i = 0; i < nvalues; ++i ) {
    char key[16];
    snprintf(key,sizeof(key),"v%u",i);
    if ( mcpl_hdr_stat_sum(fi,key) != values[i] )
      ok = 0;
    const char * c = mcpl_hdr_comment(fi,i);
    if ( strchr(c,',') )
      ok = 0;
    //(the comments are printed with the "." decimal point of the file):
    printf("%s\n",c);
  }
  mcpl_close_file(fi);
  remove("statsumlocale.mcpl");

  //mcpltool --text:
  {
    mcpl_outfile_t fo = mcpl_create_outfile("textlocale.mcpl");
    mcpl_enable_polarisation(fo);
    mcpl_particle_t * p = mcpl_get_empty_particle(fo);
    p->pdgcode = 2112;
    p->ekin = 1.5;
    p->position[0] = 0.25;
    p->direction[2] = 1.0;
    p->polarisation[1] = 0.5;
    p->time = 0.125;
    p->weight = 2.5;
    mcpl_add_particle(fo,p);
    mcpl_close_outfile(fo);
    char a0[] = "mcpltool";
    char a1[] = "--text";
    char a2[] = "textlocale.mcpl";
    char a3[] = "textlocale.txt";
    char * argv[] = { a0, a1, a2, a3, NULL };
    if ( mcpl_tool(4,argv) != 0 )
      ok = 0;
    FILE * ft = mcpltest_fopen("textlocale.txt","r");
    char line[1024];
    while ( ft && fgets(line,sizeof(line),ft) ) {
      if ( line[0] == '#' || strncmp(line,"index",5) == 0 )
        continue;
      if ( strchr(line,',') )
        ok = 0;
      printf("%s",line);
    }
    if ( ft )
      fclose(ft);
    else
      ok = 0;
    remove("textlocale.mcpl");
    remove("textlocale.txt");
  }

  printf(ok ? "All values written and read correctly\n" : "ERROR\n");
  return ok ? 0 : 1;
}
