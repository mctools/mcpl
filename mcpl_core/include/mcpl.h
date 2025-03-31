#ifndef MCPL_H
#define MCPL_H

/******************************************************************************/
/*                                                                            */
/*  This file is part of MCPL (see https://mctools.github.io/mcpl/)           */
/*                                                                            */
/*  Copyright 2015-2025 MCPL developers.                                      */
/*                                                                            */
/*  Licensed under the Apache License, Version 2.0 (the "License");           */
/*  you may not use this file except in compliance with the License.          */
/*  You may obtain a copy of the License at                                   */
/*                                                                            */
/*      http://www.apache.org/licenses/LICENSE-2.0                            */
/*                                                                            */
/*  Unless required by applicable law or agreed to in writing, software       */
/*  distributed under the License is distributed on an "AS IS" BASIS,         */
/*  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  */
/*  See the License for the specific language governing permissions and       */
/*  limitations under the License.                                            */
/*                                                                            */
/******************************************************************************/

#include <stdint.h>

//Fixme: generate:
#define MCPL_VERSION_MAJOR 1
#define MCPL_VERSION_MINOR 6
#define MCPL_VERSION_PATCH 2
#define MCPL_VERSION   10602 /* (10000*MAJOR+100*MINOR+PATCH)   */
#define MCPL_VERSION_STR "1.6.2"
#define MCPL_FORMATVERSION 3 /* Format version of written files */

#ifdef mcpl_LIB_IS_STATIC
#  define MCPL_API
#  define MCPL_LOCAL
#else
#  ifdef _WIN32
#    ifdef mcpl_EXPORTS
#      define MCPL_API __declspec(dllexport)
#    else
#      define MCPL_API __declspec(dllimport)
#    endif
#    define MCPL_LOCAL
#  else
#    if ( ( defined(__GNUC__) && __GNUC__ >= 4) || defined(__clang__) )
#      define MCPL_API    __attribute__ ((visibility ("default")))
#      define MCPL_LOCAL  __attribute__ ((visibility ("hidden")))
#    else
#      define MCPL_API
#      define MCPL_LOCAL
#    endif
#  endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

  /*********/
  /* Types */
  /*********/

#pragma pack (push, 1)

  /* The data structure representing a particle (note that persistification of */
  /* polarisation and userflags must be explicitly enabled when writing .mcpl  */
  /* files, or they will simply contain zeroes when the file is read):         */

  /* TODO typedef struct { */
  /* TODO uint8_t * data; */
  /* TODO unsigned data_size; */
  /* TODO  } mcpl_particle_userdata_t; */

  typedef struct MCPL_API {
    double ekin;            /* kinetic energy [MeV]             */
    double polarisation[3]; /* polarisation vector              */
    double position[3];     /* position [cm]                    */
    double direction[3];    /* momentum direction (unit vector) */
    double time;            /* time-stamp [millisecond]         */
    double weight;          /* weight or intensity              */
    int32_t pdgcode;    /* MC particle number from the Particle Data Group (2112=neutron, 22=gamma, ...)        */
    uint32_t userflags; /* User flags (if used, the file header should probably contain information about how). */
    /* TODO    mcpl_particle_userdata_t * userdata; *//* reserved for future usage (always NULL now) */
    /* TODO    uint8_t * userdata; *//* reserved for future usage (always NULL now) */
  } mcpl_particle_t;

#pragma pack (pop)

  typedef struct MCPL_API { void * internal; } mcpl_file_t;    /* file-object used while reading .mcpl */
  typedef struct MCPL_API { void * internal; } mcpl_outfile_t; /* file-object used while writing .mcpl */

  /****************************/
  /* Creating new .mcpl files */
  /****************************/

  /* Instantiate new file object (will also open and override specified file) */
  MCPL_API mcpl_outfile_t mcpl_create_outfile(const char * filename);

  MCPL_API const char * mcpl_outfile_filename(mcpl_outfile_t);/* filename being written to (might have had .mcpl appended) */

  /* Optionally set global options or add info to the header: */
  MCPL_API void mcpl_hdr_set_srcname(mcpl_outfile_t, const char *);/* Name of the generating application         */
  MCPL_API void mcpl_hdr_add_comment(mcpl_outfile_t, const char *);/* Add one or more human-readable comments    */
  MCPL_API void mcpl_hdr_add_data(mcpl_outfile_t, const char * key,
                                  uint32_t ldata, const char * data);/* add binary blobs by key                  */
  MCPL_API void mcpl_enable_userflags(mcpl_outfile_t);/* to write the "userflags" info                           */
  MCPL_API void mcpl_enable_polarisation(mcpl_outfile_t);/* to write the "polarisation" info                     */
  MCPL_API void mcpl_enable_doubleprec(mcpl_outfile_t);/* use double precision FP numbers in storage             */
  MCPL_API void mcpl_enable_universal_pdgcode(mcpl_outfile_t, int32_t pdgcode);/* All particles are of the same type */
  MCPL_API void mcpl_enable_universal_weight(mcpl_outfile_t, double w);/* All particles have the same weight */

  /* Optionally (but rarely skipped) add particles, by updating the info in */
  /* and then passing in a pointer to an mcpl_particle_t instance:          */
  MCPL_API void mcpl_add_particle(mcpl_outfile_t,const mcpl_particle_t*);

  /* Finally, always remember to close the file: */
  MCPL_API void mcpl_close_outfile(mcpl_outfile_t);

  /* Alternatively close with (will call mcpl_gzip_file after close). */
  /* Returns non-zero if gzipping was succesful:                      */
  MCPL_API int mcpl_closeandgzip_outfile(mcpl_outfile_t);

  /* Convenience function which returns a pointer to a nulled-out particle
     struct which can be used to edit and pass to mcpl_add_particle. It can be
     reused and will be automatically free'd when the file is closed: */
  MCPL_API mcpl_particle_t* mcpl_get_empty_particle(mcpl_outfile_t);

  /***********************/
  /* Reading .mcpl files */
  /***********************/

  /* Open file and load header information into memory, skip to the first (if */
  /* any) particle in the list:                                               */
  MCPL_API mcpl_file_t mcpl_open_file(const char * filename);

  /* Access header data: */
  MCPL_API unsigned mcpl_hdr_version(mcpl_file_t);/* file format version (not the same as MCPL_VERSION) */
  MCPL_API uint64_t mcpl_hdr_nparticles(mcpl_file_t);/* number of particles stored in file              */
  MCPL_API const char* mcpl_hdr_srcname(mcpl_file_t);/* Name of the generating application              */
  MCPL_API unsigned mcpl_hdr_ncomments(mcpl_file_t);/* number of comments stored in file                */
  MCPL_API const char * mcpl_hdr_comment(mcpl_file_t, unsigned icomment);/* access i'th comment         */
  MCPL_API int mcpl_hdr_nblobs(mcpl_file_t);
  MCPL_API const char** mcpl_hdr_blobkeys(mcpl_file_t);/* returns 0 if there are no keys */
  MCPL_API int mcpl_hdr_blob(mcpl_file_t, const char* key,
                             uint32_t* ldata, const char ** data);/* access data (returns 0 if key doesn't exist) */
  MCPL_API int mcpl_hdr_has_userflags(mcpl_file_t);
  MCPL_API int mcpl_hdr_has_polarisation(mcpl_file_t);
  MCPL_API int mcpl_hdr_has_doubleprec(mcpl_file_t);
  MCPL_API uint64_t mcpl_hdr_header_size(mcpl_file_t);/* bytes consumed by header (uncompressed) */
  MCPL_API int mcpl_hdr_particle_size(mcpl_file_t);/* bytes per particle (uncompressed)     */
  MCPL_API int32_t mcpl_hdr_universal_pdgcode(mcpl_file_t);/* returns 0 in case of per-particle pdgcode */
  MCPL_API double mcpl_hdr_universal_weight(mcpl_file_t);/* returns 0.0 in case of per-particle weights */
  MCPL_API int mcpl_hdr_little_endian(mcpl_file_t);

  /* Request pointer to particle at current location and skip forward to the next */
  /* particle. Return value will be null in case there was no particle at the     */
  /* current location (normally due to end-of-file):                              */
  MCPL_API const mcpl_particle_t* mcpl_read(mcpl_file_t);

  /* Seek and skip in particles (returns 0 when there is no particle at the new position): */
  MCPL_API int mcpl_skipforward(mcpl_file_t,uint64_t n);
  MCPL_API int mcpl_rewind(mcpl_file_t);
  MCPL_API int mcpl_seek(mcpl_file_t,uint64_t ipos);
  MCPL_API uint64_t mcpl_currentposition(mcpl_file_t);

  /* Deallocate memory and release file-handle with: */
  MCPL_API void mcpl_close_file(mcpl_file_t);

  /***********************************/
  /* Other operations on .mcpl files */
  /***********************************/

  /* Dump information about the file to std-output:                                  */
  /*   parts : 0 -> header+particle list, 1 -> just header, 2 -> just particle list. */
  /*   nlimit: maximum number of particles to list (0 for unlimited)                 */
  /*   nskip : index of first particle in the file to list.                          */
  MCPL_API void mcpl_dump(const char * file, int parts, uint64_t nskip, uint64_t nlimit);

  /* Merge contents of a list of files by concatenating all particle contents into a   */
  /* new file, file_output. This results in an error unless all meta-data and settings */
  /* in the files are identical. Also fails if file_output already exists. Note that   */
  /* the return value is a handle to the output file which has not yet been closed:    */
  MCPL_API mcpl_outfile_t mcpl_merge_files( const char* file_output,
                                            unsigned nfiles, const char ** files);

  /* Test if files could be merged by mcpl_merge_files: */
  MCPL_API int mcpl_can_merge(const char * file1, const char* file2);

  /* Similar to mcpl_merge_files, but merges two files by appending all particles in */
  /* file2 to the list in file1 (thus file1 grows while file2 stays untouched).      */
  /* Note that this requires similar version of the MCPL format of the two files, in */
  /* addition to the other checks in mcpl_can_merge().                               */
  /* Careful usage of this function can be more efficient than mcpl_merge_files.     */
  MCPL_API void mcpl_merge_inplace(const char * file1, const char* file2);

  /* Attempt to merge incompatible files, by throwing away meta-data and otherwise */
  /* selecting a configuration which is suitable to contain the data of all files. */
  /* Userflags will be discarded unless keep_userflags=1.                          */
  /* If called with compatible files, the code will fall back to calling the usual */
  /* mcpl_merge_files function instead.                                            */
  MCPL_API mcpl_outfile_t mcpl_forcemerge_files( const char* file_output,
                                                 unsigned nfiles, const char ** files,
                                                 int keep_userflags );


  /* Attempt to fix number of particles in the header of a file which was never */
  /* properly closed:                                                           */
  MCPL_API void mcpl_repair(const char * file1);

  /* For easily creating a standard mcpl-tool cmdline application (assumes */
  /* utf8-encoded strings):                                                */
  MCPL_API int mcpl_tool(int argc, char** argv);

#ifdef _WIN32
  /* Version for implementing wmain with unicode support on windows */
  MCPL_API int mcpl_tool_wchar(int argc, wchar_t** argv);
#endif

  /* Compress a file (like running gzip on the file, transforming it from  */
  /* "filename" to "filename.gz". Non-zero return value indicates success. */
  MCPL_API int mcpl_gzip_file(const char * filename);

  /* Convenience function which transfers all settings, blobs and comments to */
  /* target. Intended to make it easy to filter files via custom C code.      */
  MCPL_API void mcpl_transfer_metadata(mcpl_file_t source, mcpl_outfile_t target);

  /* Function which can be used when transferring particles from one MCPL file  */
  /* to another. A particle must have been already read from the source file    */
  /* with a call to mcpl_read(..). This function will transfer the packed par-  */
  /* ticle data exactly when possible (using mcpl_add_particle can in principle */
  /* introduce tiny numerical uncertainties due to the internal unpacking and   */
  /* repacking of direction vectors involved):                                  */
  MCPL_API void mcpl_transfer_last_read_particle(mcpl_file_t source, mcpl_outfile_t target);

  /******************/
  /* Error handling */
  /******************/

  /* Override the error handler which will get called with the error              */
  /* description. If no handler is set, errors will get printed to stdout and the */
  /* process terminated. An error handler should not return to the calling code.  */
  MCPL_API void mcpl_set_error_handler(void (*handler)(const char *));

  /**********************/
  /* Obsolete functions */
  /**********************/

  /* Functions kept for backwards compatibility. They keep working for now, but  */
  /* usage will result in a warning printed to stdout, notifying users to update */
  /* their code.                                                                 */

  MCPL_API void mcpl_merge(const char *, const char*);/* Obsolete name for mcpl_merge_inplace */
  MCPL_API int mcpl_gzip_file_rc(const char * filename);/* Obsolete name for mcpl_gzip_file */
  MCPL_API int mcpl_closeandgzip_outfile_rc(mcpl_outfile_t);/* Obsolete name for mcpl_closeandgzip_outfile_rc */
  MCPL_API int32_t mcpl_hdr_universel_pdgcode(mcpl_file_t);/* Obsolete name for mcpl_hdr_universal_pdgcode */

  /***********************************/
  /* Utilities for tool implementers */
  /***********************************/

  typedef struct MCPL_API {
    /* ok to read non-internal fields, but do not modify directly. If        */
    /* constructing a temporary object that will be initialised later, it is */
    /* recommended to null out all fields (in particular internal should be  */
    /* NULL.                                                                 */
    void* internal;
    uint64_t current_pos;/* reading this is like calling ftell(..) */
    uint32_t mode;/* first bit (bit mask 0x1) tells if file is gzipped */
  } mcpl_generic_filehandle_t;

  /* Open file. Can read gzipped files directly (must have extension ".gz") */
  MCPL_API mcpl_generic_filehandle_t mcpl_generic_fopen( const char * filename );
  /* fread/fclose as usual: */
  MCPL_API void mcpl_generic_fread( mcpl_generic_filehandle_t*,
                                    char * dest, uint64_t nbytes );
  MCPL_API void mcpl_generic_fclose( mcpl_generic_filehandle_t* );

  /* Read at most nbytes. Returns number of bytes actually read. */
  /* It is an error to try to read more that int32_max at a time */
  MCPL_API unsigned mcpl_generic_fread_try( mcpl_generic_filehandle_t*,
                                            char * dest, unsigned nbytes );

  /* Grab contents of file into buffer. If require_text is nonzero, */
  /* it must must be utf8 encoded and newlines will be normalised   */
  /* (e.g. \r or \r\n will be replaced with \n). It is recommended  */
  /* to set maxsize explicitly to a reasonable value to avoid       */
  /* potentially overflowing machine memory:                        */
  MCPL_API void mcpl_read_file_to_buffer( const char * filename,
                                          uint64_t maxsize,
                                          int require_text,
                                          uint64_t* result_size,
                                          char ** result_buf );

  /* Convert argv[0] to a program name to show in usage printouts (not MT */
  /* safe):                                                               */
  MCPL_API const char* mcpl_usage_progname( const char * argv0 );


#ifdef __cplusplus
}
#endif

#endif
