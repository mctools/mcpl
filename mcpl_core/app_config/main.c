
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

#include "mcpl_fileutils.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>
#ifdef MCPLCFGAPPHEADER
#  include MCPLCFGAPPHEADER
#else
#  include "mcplconfig_autogen.h"
#endif

typedef struct {
  mcu8str bindir;
  mcu8str shlibdir_override;
  int argc;
  char** argv;
} nccfgstate;

mcu8str mcplcfg_resolverelpath( const mcu8str* bindir,
                              const char* relpath )
{
  mcu8str rp = mcu8str_view_cstr(relpath);
  mcu8str pj = mctools_path_join(bindir,&rp);
  mcu8str res = mctools_real_path(&pj);
  if ( res.size == 0 ) {
    mcu8str_dealloc(&res);
    return pj;
  } else {
    mcu8str_dealloc( & pj );
    return res;
  }
}

mcu8str mcplcfg_thiscmdname( nccfgstate* state )
{
  mcu8str self_path = mctools_determine_exe_self_path( state->argc,
                                                       state->argv );
  mcu8str bn = mctools_basename(&self_path);
  mcu8str_dealloc(&self_path);
  if ( bn.size == 0 )
    mcu8str_append_cstr(&bn,"mcpl-config");
  return bn;
}

void mcplcfg_init_bindir( nccfgstate* state )
{
  if ( !state->bindir.c_str ) {
    mcu8str self_path = mctools_determine_exe_self_path( state->argc,
                                                         state->argv );
    state->bindir = mctools_dirname(&self_path);
    mcu8str_dealloc(&self_path);
  }
}

mcu8str mcplcfg_bindir( nccfgstate* state )
{
  mcplcfg_init_bindir(state);
  return mcu8str_copy(&(state->bindir));
}

mcu8str mcplcfg_libdir( nccfgstate* state )
{
  mcplcfg_init_bindir(state);
  return mcplcfg_resolverelpath(&(state->bindir),mcplcfg_const_bin2libdir());
}

mcu8str mcplcfg_shlibdir( nccfgstate* state )
{
  if ( state->shlibdir_override.size > 0 )
    return mcu8str_copy( &(state->shlibdir_override) );
  mcplcfg_init_bindir(state);
  return mcplcfg_resolverelpath(&(state->bindir),mcplcfg_const_bin2shlibdir());
}

mcu8str mcplcfg_shlibpath_given_shlibdir( const mcu8str* shlibdir )
{
  mcu8str shlibname = mcu8str_view_cstr(mcplcfg_const_shlibname());
  return mctools_path_join(shlibdir,&shlibname);
}

mcu8str mcplcfg_shlibpath( nccfgstate* state )
{
  if ( state->shlibdir_override.size > 0 ) {
    return mcplcfg_shlibpath_given_shlibdir( &(state->shlibdir_override) );
  } else {
    mcplcfg_init_bindir(state);
    mcu8str shlibdir = mcplcfg_resolverelpath(&(state->bindir),
                                            mcplcfg_const_bin2shlibdir());
    mcu8str res = mcplcfg_shlibpath_given_shlibdir( &shlibdir );
    mcu8str_dealloc( &shlibdir );
    return res;
  }
}

mcu8str mcplcfg_incdir( nccfgstate* state )
{
  mcplcfg_init_bindir(state);
  return mcplcfg_resolverelpath(&(state->bindir),mcplcfg_const_bin2incdir());
}

mcu8str mcplcfg_cmakedir( nccfgstate* state )
{
  mcplcfg_init_bindir(state);
  return mcplcfg_resolverelpath(&(state->bindir),mcplcfg_const_bin2cmakedir());
}

mcu8str mcplcfg_libpath_given_libdir( const mcu8str* libdir )
{
  mcu8str libname = mcu8str_view_cstr(mcplcfg_const_libname());
  return mctools_path_join(libdir,&libname);
}

mcu8str mcplcfg_libpath( nccfgstate* state )
{
  mcplcfg_init_bindir(state);
  mcu8str libdir = mcplcfg_resolverelpath(&(state->bindir),mcplcfg_const_bin2libdir());
  mcu8str res = mcplcfg_libpath_given_libdir( &libdir );
  mcu8str_dealloc( &libdir );
  return res;
}

mcu8str mcplcfg_buildflags( nccfgstate* state )
{
  mcu8str libdir = mcplcfg_libdir( state );
  mcu8str libpath = mcplcfg_libpath_given_libdir( &libdir );
  mcu8str incdir = mcplcfg_incdir( state );
#if ( defined (_WIN32) || defined (WIN32) )
  //Construct "/I$incdir $libpath"
  mcu8str res = mcu8str_create( incdir.size + libpath.size + (size_t)128 );
  mcu8str_append_cstr(&res," /I");
  mcu8str_append(&res,&incdir);
  mcu8str_append_cstr(&res," ");
  mcu8str_append(&res,&libpath);
#else
  //Construct "-Wl,-rpath,$libdir -Wl,$libpath -I$incdir"
  mcu8str res = mcu8str_create( libdir.size + libpath.size + incdir.size
                                + (size_t)128 );
  //+128 in last line for safety (+20 would be enough)
  mcu8str_append_cstr(&res,"-Wl,-rpath,");
  mcu8str_append(&res,&libdir);
  mcu8str_append_cstr(&res," -Wl,");
  mcu8str_append(&res,&libpath);
  mcu8str_append_cstr(&res," -I");
  mcu8str_append(&res,&incdir);
#endif
  mcu8str_dealloc( &libdir );
  mcu8str_dealloc( &libpath );
  mcu8str_dealloc( &incdir );
  return res;
}

char mcplcfg_decode_modeflag( const char* flag )
{
  //Decode primary mode flag
#define MCPLCFG_MODE_HELP 'h'
#define MCPLCFG_MODE_VERSION 'v'
#define MCPLCFG_MODE_INTVERSION 'i'
#define MCPLCFG_MODE_SUMMARY 'u'
#define MCPLCFG_MODE_SHOW 's'
#define MCPLCFG_MODE_INVALID '\0'
  if ( flag[0] != '-' )
    return MCPLCFG_MODE_INVALID;
  ++flag;
  if ( flag[0] == '-' ) {
    //long option
    ++flag;
#define MCPLCFG_STREQUALCONST(a,b) (a[0]==b[0] && strncmp(a,b,sizeof(b))==0)
#define MCPLCFG_STREQUAL(a,b) (a[0]==b[0] && strcmp(a,b)==0)

    if ( MCPLCFG_STREQUALCONST( flag, "show" ) )
      return MCPLCFG_MODE_SHOW;

    if ( MCPLCFG_STREQUALCONST( flag, "version" ) )
      return MCPLCFG_MODE_VERSION;

    if ( MCPLCFG_STREQUALCONST( flag, "intversion" ) )
      return MCPLCFG_MODE_INTVERSION;

    if ( MCPLCFG_STREQUALCONST( flag, "summary" ) )
      return MCPLCFG_MODE_SUMMARY;

    if ( MCPLCFG_STREQUALCONST( flag, "help" ) )
      return MCPLCFG_MODE_HELP;

    return MCPLCFG_MODE_INVALID;
  } else {
    //short option
    if (strlen(flag)!=1)
      return MCPLCFG_MODE_INVALID;
    switch( flag[0] ) {
    case 'h': return MCPLCFG_MODE_HELP;
    case 'v': return MCPLCFG_MODE_VERSION;
    case 'i': return MCPLCFG_MODE_INTVERSION;
    case 's': return MCPLCFG_MODE_SUMMARY;
    default:
      return MCPLCFG_MODE_INVALID;
    }
  }
}

typedef struct
{
  const char **data;
  int size;
} mcplcfg_strlist;

mcplcfg_strlist mcplcfg_show_item_list(void)
{
  //All options (synchronize with implementation of mcplcfg_show_item_lookup
  //function):
  static const char *theitems[] = {
    "bindir",
    "build_type",
    "buildflags",
    "cmakedir",
    "includedir",
    "intversion",
    "libdir",
    "libname",
    "libpath",
    //    "namespace",
    "shlibdir",
    "shlibname",
    "shlibpath",
    "version",
  };
  mcplcfg_strlist res;
  res.size = sizeof(theitems)/sizeof(*theitems);
  res.data = theitems;
  return res;
}

mcu8str mcplcfg_bool2str( int b )
{
  return mcu8str_view_cstr(b?"ON":"OFF");
}

mcu8str mcplcfg_show_item_lookup( nccfgstate* state,
                                const char* item )
{
  //Lookup string value of named item. Returns invalid string (with
  //c_str=nullptr) in case name not recognised. Synchronize with implementation
  //of mcplcfg_show_item_list function).

  //All options (libpath first since it might be used by e.g. the python
  //modules):
  if ( MCPLCFG_STREQUALCONST(item,"shlibpath") )
    return mcplcfg_shlibpath(state);

  if ( MCPLCFG_STREQUALCONST(item,"libpath") )
    return mcplcfg_libpath(state);

  /* if ( MCPLCFG_STREQUALCONST(item,"namespace") ) */
  /*   return mcu8str_view_cstr(mcplcfg_const_namespace()); */

  if ( MCPLCFG_STREQUALCONST(item,"version") )
    return mcu8str_view_cstr(mcplcfg_const_version());

  if ( MCPLCFG_STREQUALCONST(item,"intversion") )
    return mcu8str_view_cstr(mcplcfg_const_intversion());

  if ( MCPLCFG_STREQUALCONST(item,"bindir") )
    return mcplcfg_bindir(state);

  if ( MCPLCFG_STREQUALCONST(item,"libdir") )
    return mcplcfg_libdir(state);

  if ( MCPLCFG_STREQUALCONST(item,"shlibdir") )
    return mcplcfg_shlibdir(state);

  if ( MCPLCFG_STREQUALCONST(item,"includedir") )
    return mcplcfg_incdir(state);

  if ( MCPLCFG_STREQUALCONST(item,"buildflags") )
    return mcplcfg_buildflags( state );

  if ( MCPLCFG_STREQUALCONST(item,"libname") )
    return mcu8str_view_cstr(mcplcfg_const_libname());

  if ( MCPLCFG_STREQUALCONST(item,"shlibname") )
    return mcu8str_view_cstr(mcplcfg_const_shlibname());

  if ( MCPLCFG_STREQUALCONST(item,"cmakedir") )
    return mcplcfg_cmakedir(state);

  if ( MCPLCFG_STREQUALCONST(item,"build_type") )
    return mcu8str_view_cstr(mcplcfg_const_cmakebuildtype());

  //Get here on errors:
  mcu8str error;
  error.c_str = NULL;
  error.size = error.buflen = 0;
  error.owns_memory = 0;
  return error;
}

int mcplcfg_mode_show( nccfgstate* state,
                     const char** itemB,
                     const char** itemE )
{
  if ( !( itemE > itemB ) || MCPLCFG_STREQUALCONST(*itemB,"list") ) {
    mcplcfg_strlist items = mcplcfg_show_item_list();
    for ( int i = 0; i < items.size; ++i )
      printf("%s\n",items.data[i]);
    return 0;
  }

  for ( const char ** item = itemB; item != itemE; ++item ) {
    mcu8str res = mcplcfg_show_item_lookup( state, *item );
    if ( res.c_str ) {
      printf("%s\n",res.c_str);
      mcu8str_dealloc(&res);
      continue;
    }
    {
      //Error:
      mcu8str cmdname = mcplcfg_thiscmdname(state);
      fprintf(stderr,"%s: error: Invalid item \"%s\" requested."
              " Run with \"--show list\" for list of available items.\n",
              cmdname.c_str, *item);
      mcu8str_dealloc(&cmdname);
      return 1;
    }
  }
  return 0;
}

void mcplcfg_show_summary( nccfgstate* state )
{
  printf("MCPL v%s with configuration:\n",mcplcfg_const_version());
  printf("\n");
  mcplcfg_strlist items = mcplcfg_show_item_list();
  for ( int i = 0; i < items.size; ++i ) {
    const char * name = items.data[i];
    mcu8str result = mcplcfg_show_item_lookup( state, name );
    assert( result.c_str );
    printf(" %20s : %s\n",name,result.c_str);
    mcu8str_dealloc(&result);
  }
  printf("\n");
}

void mcplcfg_show_help( nccfgstate* state )
{
  mcu8str cmdname = mcplcfg_thiscmdname(state);
  printf("usage: %s [-h|-v|--intversion|-s|--show ITEM]\n",
         cmdname.c_str);
  printf("\n");
  printf("options:\n");
  printf("  -h, --help            Show this help message and exit\n");
  printf("\n");
  printf("  -v, --version         Show the MCPL version number and exit\n");
  printf("  -i, --intversion      Show MCPL version encoded into single integral\n");
  printf("                        number (e.g. v3.9.7 is 3009007) and exit.\n");
  printf("\n");
  printf("  -s, --summary         Print summary information about installation and exit.\n");
  printf("                        This displays all the information that is otherwise\n");
  printf("                        available via the --show flag.\n");
  printf("\n");
  printf("  --show ITEM           Print value of the requested information ITEM for the\n");
  printf("                        current MCPL installation and exit. Run with\n");
  printf("                        \"--show list\" to get a list of available ITEM values.\n");
  mcu8str_dealloc(&cmdname);
}

int mainprog( nccfgstate* state )
{
  int argc = state->argc;
  char mode = ( argc >= 2
                ? mcplcfg_decode_modeflag(state->argv[1])
                : MCPLCFG_MODE_INVALID );

  int min_nargs = mode == MCPLCFG_MODE_SHOW ? 3 : 2;
  int max_nargs = mode == MCPLCFG_MODE_SHOW ? 99 : 2;
  if ( mode == MCPLCFG_MODE_INVALID || argc > max_nargs || argc < min_nargs ) {
    mcu8str cmdname = mcplcfg_thiscmdname(state);
    fprintf(stderr,"%s: error: Missing or invalid arguments."
            " Run with --help for usage instructions.\n",cmdname.c_str);
    mcu8str_dealloc(&cmdname);
    return 1;
  }

  if ( mode == MCPLCFG_MODE_SHOW ) {
    const char ** arg0 = (const char**)&(state->argv[0]);
    const char ** argBegin = arg0 + 2;
    const char ** argEnd = arg0 + argc;
    int ec = mcplcfg_mode_show( state, argBegin, argEnd );
    return ec;
  }

  if ( mode == MCPLCFG_MODE_INTVERSION ) {
    printf("%s\n",mcplcfg_const_intversion());
  } else if ( mode == MCPLCFG_MODE_VERSION ) {
    printf("%s\n",mcplcfg_const_version());
  } else if ( mode == MCPLCFG_MODE_HELP ) {
    mcplcfg_show_help(state);
  } else {
    assert( mode == MCPLCFG_MODE_SUMMARY );
    mcplcfg_show_summary(state);
  }

  return 0;
}

int main ( int argc, char** argv )
{
  nccfgstate state;
  state.argc = argc;
  state.argv = argv;
  state.bindir.c_str = NULL;
  state.bindir.size = 0;
  state.bindir.buflen = 0;
  state.bindir.owns_memory = 0;
  state.shlibdir_override.c_str = NULL;
  state.shlibdir_override.size = 0;
  state.shlibdir_override.buflen = 0;
  state.shlibdir_override.owns_memory = 0;

  if ( mcplcfg_boolopt_expects_shlibdir_override() ) {
    //Expects hidden trailing arguments '+' 'shlibdir' (to support having
    //MCPL.dll in %PATH% on windows)
    if ( argc >= 3 && argv[argc-2][0] == '+' && argv[argc-2][1] == '\0'  ) {
      state.shlibdir_override = mcu8str_create_from_cstr( argv[argc-1] );
      state.argc -= 2;
    } else {
      mcu8str cmdname = mcplcfg_thiscmdname(&state);
      fprintf(stderr,"%s: installation error (shlibdir override absent).\n",
              cmdname.c_str);
      mcu8str_dealloc(&cmdname);
      return 1;
    }
  }

  int res = mainprog( &state );
  mcu8str_dealloc(&state.bindir);
  mcu8str_dealloc(&state.shlibdir_override);
  return res;
}
