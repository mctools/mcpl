#ifndef MCPLCPP_H
#define MCPLCPP_H

/******************************************************************************/
/*                                                                            */
/*  This file is part of MCPL (see https://mctools.github.io/mcpl/)           */
/*                                                                            */
/*  Copyright 2015-2026 MCPL developers.                                      */
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

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Header-only C++ interface to MCPL (requires C++17), built on the functions //
// of the C API with error states (the _es variants). Errors are reported as  //
// exceptions: mcpl::Error (derived from std::runtime_error), mcpl::IOError   //
// (derived from mcpl::Error) for failed I/O operations, and std::bad_alloc   //
// when memory allocation fails.                                              //
//                                                                            //
// Reading files:                                                             //
//                                                                            //
//   mcpl::MCPLFile f("input.mcpl");                                          //
//   auto temp = f.userdata_field<float>("temp");    // (if needed)           //
//   for ( auto p : f )                                                       //
//     if ( p.ekin() > 1.0 )                                                  //
//       do_something( p.position(), temp(p) );                               //
//                                                                            //
// Particles (mcpl::Particle) are lightweight views of the particle data in   //
// the file object, which are only valid until the next particle is read.     //
// Views of header data (strings, comments and blobs) are valid as long as    //
// the file object is open.                                                   //
//                                                                            //
// Writing files:                                                             //
//                                                                            //
//   mcpl::MCPLOutFile out("output.mcpl");                                    //
//   out.set_srcname("my program");                                           //
//   auto temp = out.add_userdata_field<float>("temp");    // (if needed)     //
//   auto p = out.new_particle();                                             //
//   p.set_ekin(1.5);                                                         //
//   p.set_userdata(temp,300.0f);                                             //
//   out.add(p);                                                              //
//   //... add many more particles                                            //
//   out.close();                                                             //
//                                                                            //
// Filenames can be given as std::filesystem::path objects, which work with   //
// all names on all platforms, or as strings (std::string, std::string_view   //
// or C strings), which are interpreted as UTF-8 like elsewhere in MCPL.      //
//                                                                            //
// Output files are only finished by close() or close_and_gzip(). If an       //
// mcpl::MCPLOutFile is destroyed without being closed (e.g. because of an    //
// exception), the file is left unfinished (it can often be recovered with    //
// mcpl::repair). File objects can be moved, but not copied.                  //
//                                                                            //
// Unless noted otherwise, all functions of the C API (in mcpl.h) have a      //
// counterpart here, with the same meaning.                                   //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "mcpl.h"

#if defined(_MSVC_LANG) && _MSVC_LANG > __cplusplus
#  define MCPLCPP_CPLUSPLUS _MSVC_LANG
#else
#  define MCPLCPP_CPLUSPLUS __cplusplus
#endif
#if MCPLCPP_CPLUSPLUS < 201703L
#  error "mcplcpp.h requires C++17 or later"
#endif

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <exception>
#include <filesystem>
#include <functional>
#include <initializer_list>
#include <iterator>
#include <memory>
#include <mutex>
#include <new>
#include <optional>
#include <ostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>

namespace mcpl {

  //////////////////////////////////////////////////////////////////////////////
  // Exceptions

  class Error : public std::runtime_error {
  public:
    explicit Error( const std::string& msg ) : std::runtime_error(msg) {}
  };

  class IOError : public Error {
  public:
    explicit IOError( const std::string& msg ) : Error(msg) {}
  };

  //////////////////////////////////////////////////////////////////////////////
  // Implementation details

  namespace detail {

    [[noreturn]] inline void throw_error( const mcpl_errstate_t& es )
    {
      if ( es.code == MCPL_ERROR_MEMORY )
        throw std::bad_alloc();
      if ( es.code == MCPL_ERROR_IO )
        throw IOError(es.msg);
      throw Error(es.msg);
    }

    [[noreturn]] inline void throw_runtime( const std::string& msg )
    {
      throw Error(msg);
    }

    //Sizes passed to the C API as 32 bit integers:
    inline std::uint32_t to_uint32( std::size_t n, const char * what )
    {
      if constexpr ( sizeof(std::size_t) > sizeof(std::uint32_t) ) {
        if ( n > std::size_t(0xFFFFFFFF) )
          throw_runtime(what);
      }
      return static_cast<std::uint32_t>(n);
    }

    //Error state passed to the C functions, throwing in check() in case of
    //errors:
    class ErrState {
    public:
      ErrState() noexcept { m_es.code = 0; }
      mcpl_errstate_t* get() noexcept { return &m_es; }
      operator mcpl_errstate_t*() noexcept { return &m_es; }
      void check() const { if ( m_es.code ) throw_error(m_es); }
    private:
      mcpl_errstate_t m_es;
    };

    inline std::string path_to_utf8( const std::filesystem::path& p )
    {
#if defined(__cpp_char8_t) && __cpp_char8_t >= 201811L
      std::u8string s = p.u8string();
      return std::string( reinterpret_cast<const char*>(s.data()), s.size() );
#else
      return p.u8string();
#endif
    }

    //Filenames given as std::filesystem::path, std::string, std::string_view
    //or C strings (only meant to be used for function arguments):
    class FilenameArg {
    public:
      FilenameArg( const char * s ) : m_cstr(s) {}
      FilenameArg( const std::string& s ) : m_cstr(s.c_str()) {}
      FilenameArg( std::string_view s ) : m_buf(s), m_cstr(m_buf.c_str()) {}
      FilenameArg( const std::filesystem::path& p )
        : m_buf(path_to_utf8(p)), m_cstr(m_buf.c_str()) {}
      FilenameArg( const FilenameArg& ) = delete;
      FilenameArg& operator=( const FilenameArg& ) = delete;
      const char * c_str() const noexcept { return m_cstr; }
    private:
      std::string m_buf;
      const char * m_cstr;
    };

    inline std::string to_utf8( const char * s ) { return s ? s : ""; }
    inline std::string to_utf8( const std::string& s ) { return s; }
    inline std::string to_utf8( std::string_view s ) { return std::string(s); }
    inline std::string to_utf8( const std::filesystem::path& p )
    {
      return path_to_utf8(p);
    }

    //Filenames as C strings (for the C functions taking lists of files):
    class FilenameList {
    public:
      template<class Range>
      explicit FilenameList( const Range& files )
      {
        for ( const auto& f : files )
          m_names.push_back( to_utf8(f) );
        init_ptrs();
      }
      unsigned size() const
      {
        return to_uint32( m_ptrs.size(), "too many files" );
      }
      const char ** data() noexcept { return m_ptrs.data(); }
    private:
      void init_ptrs()
      {
        m_ptrs.reserve(m_names.size());
        for ( const auto& n : m_names )
          m_ptrs.push_back( n.c_str() );
      }
      std::vector<std::string> m_names;
      std::vector<const char*> m_ptrs;
    };

    //Userdata types (as named in layouts):
    template<class T> struct UDType;
    template<> struct UDType<std::int8_t>   { static constexpr const char * name = "int8"; };
    template<> struct UDType<std::uint8_t>  { static constexpr const char * name = "uint8"; };
    template<> struct UDType<std::int16_t>  { static constexpr const char * name = "int16"; };
    template<> struct UDType<std::uint16_t> { static constexpr const char * name = "uint16"; };
    template<> struct UDType<std::int32_t>  { static constexpr const char * name = "int32"; };
    template<> struct UDType<std::uint32_t> { static constexpr const char * name = "uint32"; };
    template<> struct UDType<std::int64_t>  { static constexpr const char * name = "int64"; };
    template<> struct UDType<std::uint64_t> { static constexpr const char * name = "uint64"; };
    template<> struct UDType<float>         { static constexpr const char * name = "float32"; };
    template<> struct UDType<double>        { static constexpr const char * name = "float64"; };

    template<class T>
    constexpr bool is_ud_type_v = ( std::is_same_v<T,std::int8_t>
                                    || std::is_same_v<T,std::uint8_t>
                                    || std::is_same_v<T,std::int16_t>
                                    || std::is_same_v<T,std::uint16_t>
                                    || std::is_same_v<T,std::int32_t>
                                    || std::is_same_v<T,std::uint32_t>
                                    || std::is_same_v<T,std::int64_t>
                                    || std::is_same_v<T,std::uint64_t>
                                    || std::is_same_v<T,float>
                                    || std::is_same_v<T,double> );

    //Type of a field as in layouts, e.g. "float32" or "float32[3]":
    template<class T, std::size_t N>
    std::string ud_type_str()
    {
      std::string s = UDType<T>::name;
      if constexpr ( N > 0 ) {
        s += '[';
        s += std::to_string(N);
        s += ']';
      }
      return s;
    }

    //Print handler (the C++ function is passed as the context pointer of the C
    //handler, so it also works with several copies of this code in different
    //shared libraries - unlike a static mutex which might not):
    using PrintFct = std::function<void(const char*)>;

    extern "C" {
      inline void mcplcpp_print_trampoline( const char * msg,
                                            void * ctx ) noexcept
      {
        (*static_cast<PrintFct*>(ctx))(msg);
      }
    }

    struct PrintHandlerState {
      std::mutex mtx;
      std::unique_ptr<PrintFct> current;
    };

    inline PrintHandlerState& print_handler_state()
    {
      static PrintHandlerState state;
      return state;
    }

    //Output of dumps to a std::ostream (exceptions are rethrown after the C
    //function returns):
    struct DumpStream {
      std::ostream * os;
      std::exception_ptr eptr;
    };

    extern "C" {
      inline void mcplcpp_dump_trampoline( const char * msg,
                                           void * ctx ) noexcept
      {
        DumpStream * ds = static_cast<DumpStream*>(ctx);
        if ( ds->eptr )
          return;
        try {
          ds->os->write( msg, static_cast<std::streamsize>(std::strlen(msg)) );
        } catch (...) {
          ds->eptr = std::current_exception();
        }
      }
    }

  }//end of implementation details

  //////////////////////////////////////////////////////////////////////////////
  // Messages

  //Set a function which is called with all messages from MCPL (which by
  //default are printed to stdout). Calling with nullptr (or an empty
  //function) restores the default. Handlers should be set before using MCPL
  //from several threads, and handlers which might be called from several
  //threads must be thread safe themselves. Handlers must not throw
  //exceptions (std::terminate is called if they do):
  inline void set_print_handler( std::function<void(const char*)> handler )
  {
    auto& state = detail::print_handler_state();
    std::lock_guard<std::mutex> lock(state.mtx);
    std::unique_ptr<detail::PrintFct> previous = std::move(state.current);
    if ( handler ) {
      state.current = std::make_unique<detail::PrintFct>(std::move(handler));
      mcpl_set_print_handler_ctx( detail::mcplcpp_print_trampoline,
                                  state.current.get() );
    } else {
      mcpl_set_print_handler( nullptr );
    }
  }

  //////////////////////////////////////////////////////////////////////////////
  // Header data of files being read

  //View of a blob (bytes of data stored under a key in the header):
  class BlobView {
  public:
    BlobView() noexcept = default;
    BlobView( const std::uint8_t * bytes, std::size_t nbytes ) noexcept
      : m_data(bytes), m_size(nbytes) {}
    const std::uint8_t * data() const noexcept { return m_data; }
    std::size_t size() const noexcept { return m_size; }
    bool empty() const noexcept { return m_size == 0; }
    std::uint8_t operator[]( std::size_t i ) const noexcept { return m_data[i]; }
    const std::uint8_t * begin() const noexcept { return m_data; }
    const std::uint8_t * end() const noexcept { return m_data + m_size; }
  private:
    const std::uint8_t * m_data = nullptr;
    std::size_t m_size = 0;
  };

  //View of a list of strings in the header (comments or blob keys), which
  //supports size(), [i] and range-based for loops:
  class StringListView {
  public:
    class iterator {
    public:
      using iterator_category = std::random_access_iterator_tag;
      using value_type = std::string_view;
      using difference_type = std::ptrdiff_t;
      using pointer = void;
      using reference = std::string_view;
      iterator() noexcept = default;
      iterator( const StringListView * v, std::size_t i ) noexcept : m_v(v), m_i(i) {}
      std::string_view operator*() const { return (*m_v)[m_i]; }
      std::string_view operator[]( difference_type n ) const
      {
        return (*m_v)[ static_cast<std::size_t>( static_cast<difference_type>(m_i) + n ) ];
      }
      iterator& operator++() noexcept { ++m_i; return *this; }
      iterator operator++(int) noexcept { iterator r = *this; ++m_i; return r; }
      iterator& operator--() noexcept { --m_i; return *this; }
      iterator operator--(int) noexcept { iterator r = *this; --m_i; return r; }
      iterator& operator+=( difference_type n ) noexcept
      {
        m_i = static_cast<std::size_t>( static_cast<difference_type>(m_i) + n );
        return *this;
      }
      iterator& operator-=( difference_type n ) noexcept { return *this += -n; }
      friend iterator operator+( iterator a, difference_type n ) noexcept { return a += n; }
      friend iterator operator+( difference_type n, iterator a ) noexcept { return a += n; }
      friend iterator operator-( iterator a, difference_type n ) noexcept { return a -= n; }
      friend difference_type operator-( const iterator& a, const iterator& b ) noexcept
      {
        return static_cast<difference_type>(a.m_i) - static_cast<difference_type>(b.m_i);
      }
      friend bool operator==( const iterator& a, const iterator& b ) noexcept { return a.m_i == b.m_i; }
      friend bool operator!=( const iterator& a, const iterator& b ) noexcept { return a.m_i != b.m_i; }
      friend bool operator<( const iterator& a, const iterator& b ) noexcept { return a.m_i < b.m_i; }
      friend bool operator>( const iterator& a, const iterator& b ) noexcept { return a.m_i > b.m_i; }
      friend bool operator<=( const iterator& a, const iterator& b ) noexcept { return a.m_i <= b.m_i; }
      friend bool operator>=( const iterator& a, const iterator& b ) noexcept { return a.m_i >= b.m_i; }
    private:
      const StringListView * m_v = nullptr;
      std::size_t m_i = 0;
    };
    std::size_t size() const noexcept { return m_size; }
    bool empty() const noexcept { return m_size == 0; }
    //Throws std::out_of_range for invalid indices:
    std::string_view operator[]( std::size_t i ) const
    {
      if ( i >= m_size )
        throw std::out_of_range("index out of range");
      if ( m_keys )
        return m_keys[i];
      detail::ErrState es;
      const char * c = mcpl_hdr_comment_es( m_file, static_cast<unsigned>(i), es );
      es.check();
      return c;
    }
    iterator begin() const noexcept { return iterator(this,0); }
    iterator end() const noexcept { return iterator(this,m_size); }
  private:
    friend class MCPLFile;
    StringListView( mcpl_file_t f, std::size_t n, const char ** keys ) noexcept
      : m_file(f), m_size(n), m_keys(keys) {}
    mcpl_file_t m_file;
    std::size_t m_size;
    const char ** m_keys;//blob keys (NULL for comments)
  };

  //////////////////////////////////////////////////////////////////////////////
  // Particles

  template<class T, std::size_t N> class UserdataField;

  //Common accessors of particles (the members of mcpl_particle_t):
  template<class Derived>
  class ParticleAccessors {
  public:
    double ekin() const noexcept { return s().ekin; }
    std::array<double,3> position() const noexcept
    {
      return { s().position[0], s().position[1], s().position[2] };
    }
    std::array<double,3> direction() const noexcept
    {
      return { s().direction[0], s().direction[1], s().direction[2] };
    }
    std::array<double,3> polarisation() const noexcept
    {
      return { s().polarisation[0], s().polarisation[1], s().polarisation[2] };
    }
    double x() const noexcept { return s().position[0]; }
    double y() const noexcept { return s().position[1]; }
    double z() const noexcept { return s().position[2]; }
    double ux() const noexcept { return s().direction[0]; }
    double uy() const noexcept { return s().direction[1]; }
    double uz() const noexcept { return s().direction[2]; }
    double polx() const noexcept { return s().polarisation[0]; }
    double poly() const noexcept { return s().polarisation[1]; }
    double polz() const noexcept { return s().polarisation[2]; }
    double time() const noexcept { return s().time; }
    double weight() const noexcept { return s().weight; }
    std::int32_t pdgcode() const noexcept { return s().pdgcode; }
    std::uint32_t userflags() const noexcept { return s().userflags; }
    //The particle in the C API:
    const mcpl_particle_t& c_struct() const noexcept { return s(); }
  private:
    const mcpl_particle_t& s() const noexcept
    {
      return *static_cast<const Derived*>(this)->m_p;
    }
  };

  //Particle read from a file. This is a view of the data in the file object,
  //which is only valid until the next particle is read from the file (or the
  //file is closed). Default constructed objects (and the particles returned
  //by MCPLFile::read at the end of the file) are empty, which can be tested
  //by converting them to bool. Accessing the data of empty particles is not
  //allowed.
  class Particle : public ParticleAccessors<Particle> {
  public:
    Particle() noexcept = default;
    explicit operator bool() const noexcept { return m_p != nullptr; }
    //Raw userdata bytes (nullptr if the file has no userdata) and their
    //number (normally accessed with userdata fields instead):
    const std::uint8_t * raw_userdata() const noexcept { return m_ud; }
    std::uint32_t userdata_size() const noexcept { return m_udsize; }
  private:
    friend class ParticleAccessors<Particle>;
    friend class MCPLFile;
    Particle( const mcpl_particle_t * p, const std::uint8_t * ud,
              std::uint32_t udsize ) noexcept
      : m_p(p), m_ud(ud), m_udsize(udsize) {}
    const mcpl_particle_t * m_p = nullptr;
    const std::uint8_t * m_ud = nullptr;
    std::uint32_t m_udsize = 0;
  };

  //Particle to be added to an output file, from MCPLOutFile::new_particle.
  //This refers to data in the file object, and is only valid as long as the
  //file is open. All values are kept after adding the particle, so only
  //changed values need to be set before adding the next particle.
  class OutParticle : public ParticleAccessors<OutParticle> {
  public:
    OutParticle() noexcept = default;
    void set_ekin( double v ) noexcept { m_p->ekin = v; }
    void set_position( double posx, double posy, double posz ) noexcept
    {
      m_p->position[0] = posx; m_p->position[1] = posy;
      m_p->position[2] = posz;
    }
    void set_position( const std::array<double,3>& v ) noexcept
    {
      set_position(v[0],v[1],v[2]);
    }
    void set_direction( double dirx, double diry, double dirz ) noexcept
    {
      m_p->direction[0] = dirx; m_p->direction[1] = diry;
      m_p->direction[2] = dirz;
    }
    void set_direction( const std::array<double,3>& v ) noexcept
    {
      set_direction(v[0],v[1],v[2]);
    }
    void set_polarisation( double polarx, double polary,
                           double polarz ) noexcept
    {
      m_p->polarisation[0] = polarx; m_p->polarisation[1] = polary;
      m_p->polarisation[2] = polarz;
    }
    void set_polarisation( const std::array<double,3>& v ) noexcept
    {
      set_polarisation(v[0],v[1],v[2]);
    }
    void set_x( double v ) noexcept { m_p->position[0] = v; }
    void set_y( double v ) noexcept { m_p->position[1] = v; }
    void set_z( double v ) noexcept { m_p->position[2] = v; }
    void set_ux( double v ) noexcept { m_p->direction[0] = v; }
    void set_uy( double v ) noexcept { m_p->direction[1] = v; }
    void set_uz( double v ) noexcept { m_p->direction[2] = v; }
    void set_polx( double v ) noexcept { m_p->polarisation[0] = v; }
    void set_poly( double v ) noexcept { m_p->polarisation[1] = v; }
    void set_polz( double v ) noexcept { m_p->polarisation[2] = v; }
    void set_time( double v ) noexcept { m_p->time = v; }
    void set_weight( double v ) noexcept { m_p->weight = v; }
    void set_pdgcode( std::int32_t v ) noexcept { m_p->pdgcode = v; }
    void set_userflags( std::uint32_t v ) noexcept { m_p->userflags = v; }

    //Userdata (see UserdataField). Values of scalar fields are converted to
    //the type of the field, and values of array fields can be given as
    //std::array<T,N> (or braced lists) or T[N]. Elements of array fields can
    //also be set individually:
    template<class T, std::size_t N, class V>
    void set_userdata( const UserdataField<T,N>& field, const V& value );
    template<class T, std::size_t N, class = std::enable_if_t<(N>0)>>
    void set_userdata( const UserdataField<T,N>& field,
                       const std::array<T,N>& values );
    template<class T, std::size_t N>
    void set_userdata( const UserdataField<T,N>& field, std::size_t i,
                       T value );

    //The particle in the C API (for direct modification):
    mcpl_particle_t& c_struct() noexcept { return *m_p; }
    using ParticleAccessors<OutParticle>::c_struct;

    std::uint8_t * raw_userdata() noexcept { return m_ud; }
    const std::uint8_t * raw_userdata() const noexcept { return m_ud; }
    std::uint32_t userdata_size() const noexcept { return m_udsize; }
  private:
    friend class ParticleAccessors<OutParticle>;
    friend class MCPLOutFile;
    OutParticle( mcpl_particle_t * p, std::uint8_t * ud, std::uint32_t udsize,
                 const void * owner ) noexcept
      : m_p(p), m_ud(ud), m_udsize(udsize), m_owner(owner) {}
    mcpl_particle_t * m_p = nullptr;
    std::uint8_t * m_ud = nullptr;
    std::uint32_t m_udsize = 0;
    const void * m_owner = nullptr;
  };

  //////////////////////////////////////////////////////////////////////////////
  // Userdata fields

  //Access to a field of the userdata of particles, with values of type T
  //(std::int8_t, std::uint8_t, ..., std::uint64_t, float or double for the
  //types int8, uint8, ..., uint64, float32 or float64), or arrays of N such
  //values. Objects are obtained from MCPLFile::userdata_field or from
  //MCPLOutFile::add_userdata_field (or MCPLOutFile::userdata_field), which
  //check that the field exists with exactly this type. Values are read with
  //field(particle) (and array elements with field(particle,i)), and set with
  //OutParticle::set_userdata. Fields can be used with particles from any file
  //(e.g. when reading several files with the same layout), but give errors
  //if the userdata of the particle is too short.
  template<class T, std::size_t N = 0>
  class UserdataField {
    static_assert( detail::is_ud_type_v<T>,
                   "Userdata fields must have type std::int8_t, std::uint8_t,"
                   " std::int16_t, std::uint16_t, std::int32_t, std::uint32_t,"
                   " std::int64_t, std::uint64_t, float or double" );
  public:
    static constexpr std::size_t nvalues = ( N == 0 ? 1 : N );
    static constexpr std::size_t nbytes = nvalues * sizeof(T);
    //Scalar fields (N==0) give values of type T, and array fields give
    //std::array<T,N>:
    using value_type = std::conditional_t< N == 0, T, std::array<T,(N==0?1:N)> >;

    UserdataField() noexcept = default;
    std::uint32_t offset() const noexcept { return m_offset; }
    std::size_t size() const noexcept { return nvalues; }

    value_type operator()( const Particle& p ) const
    {
      return get( p.raw_userdata(), p.userdata_size() );
    }
    value_type operator()( const OutParticle& p ) const
    {
      return get( p.raw_userdata(), p.userdata_size() );
    }
    //Element i of array fields (std::out_of_range if i>=N):
    T operator()( const Particle& p, std::size_t i ) const
    {
      return get_element( p.raw_userdata(), p.userdata_size(), i );
    }
    T operator()( const OutParticle& p, std::size_t i ) const
    {
      return get_element( p.raw_userdata(), p.userdata_size(), i );
    }

  private:
    friend class MCPLFile;
    friend class MCPLOutFile;
    friend class OutParticle;
    explicit UserdataField( std::uint32_t offset ) noexcept : m_offset(offset) {}

    void check( const void * ud, std::uint32_t udsize ) const
    {
      if ( !ud || static_cast<std::uint64_t>(m_offset) + nbytes > udsize )
        detail::throw_runtime( ud ? "userdata of particle is too short for"
                                    " the userdata field"
                                  : "particle has no userdata" );
    }
    value_type get( const std::uint8_t * ud, std::uint32_t udsize ) const
    {
      check(ud,udsize);
      value_type v;
      std::memcpy( &v, ud + m_offset, nbytes );
      return v;
    }
    T get_element( const std::uint8_t * ud, std::uint32_t udsize,
                   std::size_t i ) const
    {
      static_assert( N > 0, "element access is only for array fields" );
      if ( i >= N )
        throw std::out_of_range("userdata array index out of range");
      check(ud,udsize);
      T v;
      std::memcpy( &v, ud + m_offset + i * sizeof(T), sizeof(T) );
      return v;
    }
    void set( std::uint8_t * ud, std::uint32_t udsize, const T * values ) const
    {
      check(ud,udsize);
      std::memcpy( ud + m_offset, values, nbytes );
    }
    void set_element( std::uint8_t * ud, std::uint32_t udsize,
                      std::size_t i, T value ) const
    {
      static_assert( N > 0, "element access is only for array fields" );
      if ( i >= N )
        throw std::out_of_range("userdata array index out of range");
      check(ud,udsize);
      std::memcpy( ud + m_offset + i * sizeof(T), &value, sizeof(T) );
    }
    std::uint32_t m_offset = 0;
  };

  template<class T, std::size_t N, class V>
  inline void OutParticle::set_userdata( const UserdataField<T,N>& field,
                                         const V& value )
  {
    if constexpr ( N == 0 ) {
      static_assert( std::is_convertible_v<V,T>,
                     "value can not be converted to the type of the field" );
      const T v = static_cast<T>(value);
      field.set( m_ud, m_udsize, &v );
    } else if constexpr ( std::is_same_v<V,T[N]> ) {
      field.set( m_ud, m_udsize, &value[0] );
    } else {
      static_assert( std::is_same_v<V,std::array<T,N>>,
                     "values of array fields must be given as std::array<T,N>"
                     " or T[N]" );
    }
  }

  template<class T, std::size_t N, class>
  inline void OutParticle::set_userdata( const UserdataField<T,N>& field,
                                         const std::array<T,N>& values )
  {
    field.set( m_ud, m_udsize, values.data() );
  }

  template<class T, std::size_t N>
  inline void OutParticle::set_userdata( const UserdataField<T,N>& field,
                                         std::size_t i, T value )
  {
    field.set_element( m_ud, m_udsize, i, value );
  }

  //////////////////////////////////////////////////////////////////////////////
  // Reading files

  //Parts of files shown by dump():
  enum class DumpParts { All = 0, Header = 1, Particles = 2 };

  //Whether forcemerge_files keeps the userflags of particles:
  enum class KeepUserflags { No, Yes };

  class MCPLFile {
  public:
    //Open the file:
    explicit MCPLFile( detail::FilenameArg filename )
    {
      detail::ErrState es;
      m_f = mcpl_open_file_es( filename.c_str(), es );
      if ( es.get()->code ) {
        mcpl_close_file( m_f );
        es.check();
      }
      m_udsize = mcpl_hdr_userdata_size( m_f );
    }
    ~MCPLFile() { close(); }
    MCPLFile( const MCPLFile& ) = delete;
    MCPLFile& operator=( const MCPLFile& ) = delete;
    MCPLFile( MCPLFile&& o ) noexcept : m_f(o.m_f), m_udsize(o.m_udsize)
    {
      o.m_f.internal = nullptr;
    }
    MCPLFile& operator=( MCPLFile&& o ) noexcept
    {
      if ( this != &o ) {
        close();
        m_f = o.m_f;
        m_udsize = o.m_udsize;
        o.m_f.internal = nullptr;
      }
      return *this;
    }

    //Close the file (it is closed automatically when destroyed):
    void close() noexcept
    {
      if ( m_f.internal ) {
        mcpl_close_file( m_f );
        m_f.internal = nullptr;
      }
    }
    bool is_open() const noexcept { return m_f.internal != nullptr; }

    //Header data (string views are valid as long as the file is open):
    unsigned version() const { return mcpl_hdr_version( h() ); }
    std::uint64_t nparticles() const { return mcpl_hdr_nparticles( h() ); }
    std::string_view srcname() const { return mcpl_hdr_srcname( h() ); }
    std::size_t ncomments() const { return mcpl_hdr_ncomments( h() ); }
    std::string_view comment( std::size_t i ) const { return comments()[i]; }
    StringListView comments() const
    {
      mcpl_file_t f = h();
      return StringListView( f, mcpl_hdr_ncomments( f ), nullptr );
    }
    std::size_t nblobs() const
    {
      return static_cast<std::size_t>( mcpl_hdr_nblobs( h() ) );
    }
    StringListView blob_keys() const
    {
      const char ** keys = mcpl_hdr_blobkeys( h() );
      return StringListView( m_f, keys ? nblobs() : 0, keys );
    }
    bool has_blob( std::string_view key ) const
    {
      uint32_t ldata;
      const char * data;
      return mcpl_hdr_blob( h(), std::string(key).c_str(), &ldata, &data ) != 0;
    }
    //Throws mcpl::Error if there is no blob with the key:
    BlobView blob( std::string_view key ) const
    {
      uint32_t ldata = 0;
      const char * data = nullptr;
      std::string k(key);
      if ( !mcpl_hdr_blob( h(), k.c_str(), &ldata, &data ) )
        detail::throw_runtime( "no blob with key \"" + k + "\"" );
      return BlobView( reinterpret_cast<const std::uint8_t*>(data), ldata );
    }
    bool has_userflags() const { return mcpl_hdr_has_userflags( h() ) != 0; }
    bool has_polarisation() const { return mcpl_hdr_has_polarisation( h() ) != 0; }
    bool has_doubleprec() const { return mcpl_hdr_has_doubleprec( h() ) != 0; }
    std::uint64_t header_size() const { return mcpl_hdr_header_size( h() ); }
    int particle_size() const { return mcpl_hdr_particle_size( h() ); }
    //0 if particles have individual pdgcodes:
    std::int32_t universal_pdgcode() const { return mcpl_hdr_universal_pdgcode( h() ); }
    //0.0 if particles have individual weights:
    double universal_weight() const { return mcpl_hdr_universal_weight( h() ); }
    bool little_endian() const { return mcpl_hdr_little_endian( h() ) != 0; }

    //Statistics "sum" by key. stat_sum returns an empty value if the entry
    //exists but its value is not available (-1 in the file, e.g. if the
    //program writing the file crashed), and throws mcpl::Error if there is
    //no entry with the key:
    bool has_stat_sum( std::string_view key ) const
    {
      return stat_sum_raw(key) != -2.0;
    }
    std::optional<double> stat_sum( std::string_view key ) const
    {
      double v = stat_sum_raw(key);
      if ( v == -2.0 )
        detail::throw_runtime( "no stat:sum entry with key \""
                               + std::string(key) + "\"" );
      if ( v == -1.0 )
        return std::nullopt;
      return v;
    }

    //Userdata layout (empty if the file has no userdata) and the number of
    //bytes per particle:
    std::string_view userdata_layout() const
    {
      const char * l = mcpl_hdr_userdata_layout( h() );
      return l ? l : std::string_view();
    }
    std::uint32_t userdata_size() const { h(); return m_udsize; }

    //Field in the userdata, which must exist with exactly this type (e.g.
    //userdata_field<float>("temp") for "temp:float32", or
    //userdata_field<float,3>("dir") for "dir:float32[3]"):
    template<class T, std::size_t N = 0>
    UserdataField<T,N> userdata_field( std::string_view name ) const
    {
      const char * l = mcpl_hdr_userdata_layout( h() );
      if ( !l )
        detail::throw_runtime( "file has no userdata" );
      detail::ErrState es;
      std::uint32_t off = mcpl_userdata_offset_es( l, std::string(name).c_str(),
                                                   detail::ud_type_str<T,N>().c_str(),
                                                   es );
      es.check();
      return UserdataField<T,N>(off);
    }

    //Read the next particle (an empty particle at the end of the file):
    Particle read()
    {
      detail::ErrState es;
      const std::uint8_t * ud = nullptr;
      const mcpl_particle_t * p = mcpl_read_with_userdata_es( h(), &ud, es );
      es.check();
      return Particle( p, ud, ud ? m_udsize : 0 );
    }

    //Skip forward or go to a position (returning false if there is no
    //particle at the new position):
    bool skip_forward( std::uint64_t n )
    {
      detail::ErrState es;
      int r = mcpl_skipforward_es( h(), n, es );
      es.check();
      return r != 0;
    }
    bool rewind()
    {
      detail::ErrState es;
      int r = mcpl_rewind_es( h(), es );
      es.check();
      return r != 0;
    }
    bool seek( std::uint64_t ipos )
    {
      detail::ErrState es;
      int r = mcpl_seek_es( h(), ipos, es );
      es.check();
      return r != 0;
    }
    std::uint64_t current_position() const { return mcpl_currentposition( h() ); }

    //Range-based for loops over the particles, from the current position:
    class iterator {
    public:
      using iterator_category = std::input_iterator_tag;
      using value_type = Particle;
      using difference_type = std::ptrdiff_t;
      using pointer = const Particle*;
      using reference = const Particle&;
      iterator() noexcept = default;
      const Particle& operator*() const noexcept { return m_p; }
      const Particle* operator->() const noexcept { return &m_p; }
      iterator& operator++() { m_p = m_f->read(); return *this; }
      iterator operator++(int) { iterator r = *this; ++*this; return r; }
      friend bool operator==( const iterator& a, const iterator& b ) noexcept
      {
        return !a.m_p && !b.m_p;
      }
      friend bool operator!=( const iterator& a, const iterator& b ) noexcept
      {
        return !( a == b );
      }
    private:
      friend class MCPLFile;
      explicit iterator( MCPLFile * f ) : m_f(f), m_p(f->read()) {}
      MCPLFile * m_f = nullptr;
      Particle m_p;
    };
    iterator begin() { return iterator(this); }
    iterator end() noexcept { return iterator(); }

    //Dump information about the file (like mcpl_dump, with nlimit=0 meaning
    //no limit), to the print handler or to a stream. The position in the file
    //is not changed, but particles read before are no longer valid
    //afterwards (also for MCPLOutFile::transfer_last_read_particle):
    void dump( DumpParts parts = DumpParts::All, std::uint64_t nskip = 0,
               std::uint64_t nlimit = 0 )
    {
      detail::ErrState es;
      mcpl_dump_file_es( h(), static_cast<int>(parts), nskip, nlimit,
                         nullptr, nullptr, es );
      es.check();
    }
    void dump( std::ostream& os, DumpParts parts = DumpParts::All,
               std::uint64_t nskip = 0, std::uint64_t nlimit = 0 )
    {
      detail::ErrState es;
      detail::DumpStream ds{ &os, nullptr };
      mcpl_dump_file_es( h(), static_cast<int>(parts), nskip, nlimit,
                         detail::mcplcpp_dump_trampoline, &ds, es );
      if ( ds.eptr )
        std::rethrow_exception( ds.eptr );
      es.check();
    }

    //The file object in the C API (for direct use with the C functions):
    mcpl_file_t c_handle() const noexcept { return m_f; }

  private:
    //Handle for the C functions without error states (which do not check for
    //invalid handles):
    mcpl_file_t h() const
    {
      if ( !m_f.internal )
        detail::throw_runtime( "MCPLFile object is not open" );
      return m_f;
    }
    double stat_sum_raw( std::string_view key ) const
    {
      detail::ErrState es;
      double v = mcpl_hdr_stat_sum_es( h(), std::string(key).c_str(), es );
      es.check();
      return v;
    }
    mcpl_file_t m_f = { nullptr };
    std::uint32_t m_udsize = 0;
  };

  //////////////////////////////////////////////////////////////////////////////
  // Writing files

  class MCPLOutFile {
  public:
    //Create the file (.mcpl is appended to the name if it does not already
    //end with .mcpl):
    explicit MCPLOutFile( detail::FilenameArg filename )
    {
      detail::ErrState es;
      m_f = mcpl_create_outfile_es( filename.c_str(), es );
      if ( es.get()->code ) {
        detail::ErrState ignored;
        mcpl_close_outfile_unfinished_es( m_f, ignored );
        m_f.internal = nullptr;
        es.check();
      }
    }
    //Leaves the file unfinished unless it was closed:
    ~MCPLOutFile() { abandon(); }
    MCPLOutFile( const MCPLOutFile& ) = delete;
    MCPLOutFile& operator=( const MCPLOutFile& ) = delete;
    MCPLOutFile( MCPLOutFile&& o ) noexcept
      : m_f(o.m_f), m_pending_layout(std::move(o.m_pending_layout)),
        m_ud(std::move(o.m_ud)), m_puser(o.m_puser),
        m_layout_locked(o.m_layout_locked)
    {
      o.m_f.internal = nullptr;
      o.m_puser = nullptr;
      o.m_layout_locked = false;
    }
    MCPLOutFile& operator=( MCPLOutFile&& o ) noexcept
    {
      if ( this != &o ) {
        abandon();
        m_f = o.m_f;
        m_pending_layout = std::move(o.m_pending_layout);
        m_ud = std::move(o.m_ud);
        m_puser = o.m_puser;
        m_layout_locked = o.m_layout_locked;
        o.m_f.internal = nullptr;
        o.m_puser = nullptr;
        o.m_layout_locked = false;
      }
      return *this;
    }

    //Finish and close the file (optionally gzipping it). Errors leave the
    //file unfinished, and the object is closed in any case. Does nothing if
    //the file is not open:
    void close()
    {
      if ( !m_f.internal )
        return;
      finalise_layout_for_closing();
      detail::ErrState es;
      mcpl_outfile_t f = release();
      mcpl_close_outfile_es( f, es );
      es.check();
    }
    void close_and_gzip()
    {
      if ( !m_f.internal )
        return;
      finalise_layout_for_closing();
      detail::ErrState es;
      mcpl_outfile_t f = release();
      mcpl_closeandgzip_outfile_es( f, es );
      es.check();
    }
    //Close the file without finishing it (like the destructor), leaving it
    //unfinished. Errors are ignored:
    void abandon() noexcept
    {
      if ( m_f.internal ) {
        //(an error state must be given, since errors would otherwise go to
        //the error handler, which by default ends the program):
        detail::ErrState ignored;
        mcpl_close_outfile_unfinished_es( release(), ignored );
      }
    }
    bool is_open() const noexcept { return m_f.internal != nullptr; }

    //Name of the file (valid as long as the file is open):
    std::string_view filename() const { return mcpl_outfile_filename( h() ); }

    //Header data and options (which must be set before adding particles):
    void set_srcname( std::string_view name )
    {
      call( mcpl_hdr_set_srcname_es, std::string(name).c_str() );
    }
    void add_comment( std::string_view comment )
    {
      call( mcpl_hdr_add_comment_es, std::string(comment).c_str() );
    }
    void add_blob( std::string_view key, const void * data, std::size_t size )
    {
      call( mcpl_hdr_add_data_es, std::string(key).c_str(),
            detail::to_uint32( size, "blob too large" ),
            static_cast<const char*>(data) );
    }
    void add_blob( std::string_view key, const std::vector<std::uint8_t>& data )
    {
      add_blob( key, data.data(), data.size() );
    }
    void add_blob( std::string_view key, std::string_view data )
    {
      add_blob( key, data.data(), data.size() );
    }
    void enable_userflags() { call( mcpl_enable_userflags_es ); }
    void enable_polarisation() { call( mcpl_enable_polarisation_es ); }
    void enable_doubleprec() { call( mcpl_enable_doubleprec_es ); }
    void enable_universal_pdgcode( std::int32_t pdgcode )
    {
      call( mcpl_enable_universal_pdgcode_es, pdgcode );
    }
    void enable_universal_weight( double w )
    {
      call( mcpl_enable_universal_weight_es, w );
    }

    //Statistics "sum": the value must be non-negative, and can be added again
    //later to update it. Entries can be reserved with reserve_stat_sum (when
    //the value is not yet known), but a value must then be added before
    //closing the file:
    void add_stat_sum( std::string_view key, double value )
    {
      if ( !( value >= 0.0 ) )
        detail::throw_runtime( "stat:sum values must be non-negative (use"
                               " reserve_stat_sum to reserve entries)" );
      call( mcpl_hdr_add_stat_sum_es, std::string(key).c_str(), value );
    }
    void reserve_stat_sum( std::string_view key )
    {
      call( mcpl_hdr_add_stat_sum_es, std::string(key).c_str(), -1.0 );
    }
    //Scale all stat:sum entries with a finite factor >0 (or -1 to mark them
    //all as not available), like mcpl_hdr_scale_stat_sums:
    void scale_stat_sums( double scale )
    {
      call( mcpl_hdr_scale_stat_sums_es, scale );
    }

    //Userdata. Fields are added one at a time with add_userdata_field, which
    //returns the object for setting their values (e.g.
    //add_userdata_field<float>("temp") for a field "temp:float32", or
    //add_userdata_field<float,3>("dir") for "dir:float32[3]"). Alternatively,
    //the whole layout can be given with enable_userdata. The layout is fixed
    //when particles are added (or new_particle is called), after which no
    //fields can be added:
    template<class T, std::size_t N = 0>
    UserdataField<T,N> add_userdata_field( std::string_view name )
    {
      h();
      if ( m_layout_locked || mcpl_outfile_userdata_layout( m_f ) )
        detail::throw_runtime( "userdata fields can not be added after the"
                               " userdata layout is fixed" );
      std::string field = std::string(name) + ":" + detail::ud_type_str<T,N>();
      std::string layout = m_pending_layout.empty()
        ? field : m_pending_layout + "," + field;
      detail::ErrState es;
      //(validates the layout, e.g. names and duplicates):
      mcpl_userdata_layout_size_es( layout.c_str(), es );
      es.check();
      std::uint32_t off = mcpl_userdata_offset_es( layout.c_str(),
                                                   std::string(name).c_str(),
                                                   detail::ud_type_str<T,N>().c_str(),
                                                   es );
      es.check();
      m_pending_layout = std::move(layout);
      return UserdataField<T,N>(off);
    }
    void enable_userdata( std::string_view layout )
    {
      h();
      if ( !m_pending_layout.empty() )
        detail::throw_runtime( "enable_userdata can not be used after"
                               " add_userdata_field" );
      if ( m_layout_locked )
        detail::throw_runtime( "enable_userdata must be called before"
                               " particles are added (or new_particle is"
                               " called)" );
      call( mcpl_enable_userdata_es, std::string(layout).c_str() );
      update_userdata_buffer();
    }
    //Layout of the userdata (empty if none):
    std::string userdata_layout() const
    {
      const char * l = mcpl_outfile_userdata_layout( h() );
      return l ? std::string(l) : m_pending_layout;
    }
    //Field in an already given layout (e.g. from enable_userdata or
    //transfer_metadata):
    template<class T, std::size_t N = 0>
    UserdataField<T,N> userdata_field( std::string_view name ) const
    {
      std::string layout = userdata_layout();
      if ( layout.empty() )
        detail::throw_runtime( "file has no userdata" );
      detail::ErrState es;
      std::uint32_t off = mcpl_userdata_offset_es( layout.c_str(),
                                                   std::string(name).c_str(),
                                                   detail::ud_type_str<T,N>().c_str(),
                                                   es );
      es.check();
      return UserdataField<T,N>(off);
    }

    //The particle object of the file, reset to zero (also the userdata). It
    //is the same object every time, and is valid as long as the file is
    //open:
    OutParticle new_particle()
    {
      h();
      fix_layout();
      if ( !m_puser ) {
        detail::ErrState es;
        m_puser = mcpl_get_empty_particle_es( m_f, es );
        es.check();
      }
      std::memset( m_puser, 0, sizeof(mcpl_particle_t) );
      if ( !m_ud.empty() )
        std::memset( m_ud.data(), 0, m_ud.size() );
      return OutParticle( m_puser, m_ud.empty() ? nullptr : m_ud.data(),
                          static_cast<std::uint32_t>(m_ud.size()),
                          m_f.internal );
    }

    //Add the particle (with its userdata, if the file has userdata):
    void add( const OutParticle& p )
    {
      h();
      if ( p.m_owner != m_f.internal )
        detail::throw_runtime( "particle does not belong to this output file" );
      add_impl( p.c_struct(), p.m_ud );
    }
    //Add a particle given as in the C API (with all userdata bytes zero, if
    //the file has userdata):
    void add( const mcpl_particle_t& p )
    {
      h();
      fix_layout();
      add_impl( p, nullptr );
    }

    //Transfer all header data and settings from a file being read (like
    //mcpl_transfer_metadata), and the last particle read from it (like
    //mcpl_transfer_last_read_particle):
    void transfer_metadata( const MCPLFile& source )
    {
      h();
      if ( m_layout_locked )
        detail::throw_runtime( "transfer_metadata must be called before"
                               " particles are added (or new_particle is"
                               " called)" );
      fix_pending_layout();
      detail::ErrState es;
      mcpl_transfer_metadata_es( source.c_handle(), m_f, es );
      es.check();
      update_userdata_buffer();
    }
    void transfer_last_read_particle( const MCPLFile& source )
    {
      h();
      fix_layout();
      detail::ErrState es;
      mcpl_transfer_last_read_particle_es( source.c_handle(), m_f, es );
      es.check();
    }

    //The file object in the C API (for direct use with the C functions):
    mcpl_outfile_t c_handle() const noexcept { return m_f; }

  private:
    friend MCPLOutFile merge_files( detail::FilenameArg,
                                    detail::FilenameList&& );
    friend MCPLOutFile forcemerge_files( detail::FilenameArg,
                                         detail::FilenameList&&,
                                         KeepUserflags );
    explicit MCPLOutFile( mcpl_outfile_t f ) : m_f(f), m_layout_locked(true)
    {
      try {
        update_userdata_buffer();
      } catch (...) {
        abandon();
        throw;
      }
    }

    mcpl_outfile_t h() const
    {
      if ( !m_f.internal )
        detail::throw_runtime( "MCPLOutFile object is not open" );
      return m_f;
    }
    template<class Fct, class... Args>
    void call( Fct fct, Args... args )
    {
      detail::ErrState es;
      fct( h(), args..., es );
      es.check();
    }
    mcpl_outfile_t release() noexcept
    {
      mcpl_outfile_t f = m_f;
      m_f.internal = nullptr;
      m_puser = nullptr;
      m_ud.clear();
      m_pending_layout.clear();
      m_layout_locked = false;
      return f;
    }
    //Give any fields added with add_userdata_field to the C library:
    void fix_pending_layout()
    {
      h();
      if ( !m_pending_layout.empty() ) {
        call( mcpl_enable_userdata_es, m_pending_layout.c_str() );
        m_pending_layout.clear();
      }
      update_userdata_buffer();
    }
    //Fix the layout before particles are added:
    void fix_layout()
    {
      if ( !m_layout_locked ) {
        fix_pending_layout();
        m_layout_locked = true;
      }
    }
    void finalise_layout_for_closing()
    {
      //(errors are only reported, the file is closed by the caller anyway):
      if ( m_f.internal && !m_pending_layout.empty() ) {
        detail::ErrState es;
        mcpl_enable_userdata_es( m_f, m_pending_layout.c_str(), es );
        m_pending_layout.clear();
        if ( es.get()->code ) {
          abandon();
          es.check();
        }
      }
    }
    void update_userdata_buffer()
    {
      const char * l = mcpl_outfile_userdata_layout( m_f );
      std::uint32_t n = 0;
      if ( l ) {
        detail::ErrState es;
        n = mcpl_userdata_layout_size_es( l, es );
        es.check();
      }
      if ( m_ud.size() != n )
        m_ud.assign( n, 0 );
    }
    void add_impl( const mcpl_particle_t& p, const std::uint8_t * ud )
    {
      detail::ErrState es;
      if ( !m_ud.empty() )
        mcpl_add_particle_with_userdata_es( m_f, &p, ud, es );
      else
        mcpl_add_particle_es( m_f, &p, es );
      es.check();
    }

    mcpl_outfile_t m_f = { nullptr };
    std::string m_pending_layout;//fields not yet given to the C library
    std::vector<std::uint8_t> m_ud;//userdata of new_particle()
    mcpl_particle_t * m_puser = nullptr;
    bool m_layout_locked = false;//set when particles can be added
  };

  //////////////////////////////////////////////////////////////////////////////
  // Operations on files. Lists of files can be given as containers (like
  // std::vector) of C strings, std::string, std::string_view or
  // std::filesystem::path, or as initializer lists like {"a.mcpl","b.mcpl"}.

  //Merge files into a new file (which must not exist), like mcpl_merge_files.
  //The returned output file must be closed by calling .close() (but can have
  //more particles added first):
  inline MCPLOutFile merge_files( detail::FilenameArg file_output,
                                  detail::FilenameList&& files )
  {
    detail::ErrState es;
    mcpl_outfile_t f = mcpl_merge_files_es( file_output.c_str(), files.size(),
                                            files.data(), es );
    es.check();
    return MCPLOutFile(f);
  }
  template<class Range>
  inline MCPLOutFile merge_files( detail::FilenameArg file_output,
                                  const Range& files )
  {
    return merge_files( file_output.c_str(), detail::FilenameList(files) );
  }
  inline MCPLOutFile merge_files( detail::FilenameArg file_output,
                                  std::initializer_list<detail::FilenameArg> files )
  {
    std::vector<std::string> names;
    for ( const auto& f : files )
      names.emplace_back( f.c_str() );
    return merge_files( file_output.c_str(), detail::FilenameList(names) );
  }

  //Merge files with different settings, discarding metadata if needed (like
  //mcpl_forcemerge_files):
  inline MCPLOutFile forcemerge_files( detail::FilenameArg file_output,
                                       detail::FilenameList&& files,
                                       KeepUserflags keep_userflags )
  {
    detail::ErrState es;
    mcpl_outfile_t f = mcpl_forcemerge_files_es( file_output.c_str(),
                                                 files.size(), files.data(),
                                                 keep_userflags == KeepUserflags::Yes
                                                 ? 1 : 0, es );
    es.check();
    return MCPLOutFile(f);
  }
  template<class Range>
  inline MCPLOutFile forcemerge_files( detail::FilenameArg file_output,
                                       const Range& files,
                                       KeepUserflags keep_userflags = KeepUserflags::No )
  {
    return forcemerge_files( file_output.c_str(), detail::FilenameList(files),
                             keep_userflags );
  }
  inline MCPLOutFile forcemerge_files( detail::FilenameArg file_output,
                                       std::initializer_list<detail::FilenameArg> files,
                                       KeepUserflags keep_userflags = KeepUserflags::No )
  {
    std::vector<std::string> names;
    for ( const auto& f : files )
      names.emplace_back( f.c_str() );
    return forcemerge_files( file_output.c_str(), detail::FilenameList(names),
                             keep_userflags );
  }

  //Whether two files can be merged:
  inline bool can_merge( detail::FilenameArg file1, detail::FilenameArg file2 )
  {
    detail::ErrState es;
    int r = mcpl_can_merge_es( file1.c_str(), file2.c_str(), es );
    es.check();
    return r != 0;
  }

  //Append the particles of file2 to file1:
  inline void merge_inplace( detail::FilenameArg file1,
                             detail::FilenameArg file2 )
  {
    detail::ErrState es;
    mcpl_merge_inplace_es( file1.c_str(), file2.c_str(), es );
    es.check();
  }

  //Repair a file which was not properly closed:
  inline void repair( detail::FilenameArg filename )
  {
    detail::ErrState es;
    mcpl_repair_es( filename.c_str(), es );
    es.check();
  }

  //Compress a file (replacing filename with filename.gz):
  inline void gzip_file( detail::FilenameArg filename )
  {
    detail::ErrState es;
    mcpl_gzip_file_es( filename.c_str(), es );
    es.check();
  }

}

#endif
