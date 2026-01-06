
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

#include "mcpl.h"
#include <iostream>
#include <fstream>
#include <cstring>

namespace {

  void writeFile( const char * fn, const char* content, std::size_t n )
  {
    std::ofstream fs(fn, std::ios::out | std::ios::binary | std::ios::trunc );
    if (n)
      fs.write(content, n);
    fs.close();
  }
  std::string fmtText( const char* content, std::size_t n )
  {
    std::string r;
    r += '"';
    const char* c = content;
    const char* cE = c + n;
    std::size_t i = 0;
    for ( ; c!=cE; ++c ) {
      ++i;
      if ( n > 200 ) {
        if ( i > 30 && i+30 < n ) {
          if ( i == 31 )
            r+="@@SNIP@@";
          continue;
        }
      }
      if ( *c == '\r' )
        r += "<R>";
      else if ( *c == '\n' )
        r += "<N>";
      else
        r += *c;
    }
    r += '"';
    return r;
  }
  std::string fmtText( const std::string& s )
  {
    return fmtText( s.c_str(), s.size() );
  }
  void testData( const char* content, std::size_t n, bool is_text = false )
  {
    static int itd = 1;
    printf("\n\n----> TestData #%i\n",itd++);
    const char* ref_content = content;
    std::size_t ref_n = n;
    std::size_t reduced_maxsize =  ( n/2 ? n/2 : 1 );
    if ( reduced_maxsize > n )
      reduced_maxsize = n;

    std::string expected_text_content, expected_text_content_reducedmaxsize;
    if ( is_text ) {
      auto calcExpectedTextCont = [](const char* content,
                                     std::size_t nn)
      {
        std::string r;
        if ( !nn )
          return r;
        r.resize( nn );
        char * tmpbuf = &r[0];
        char * itO = tmpbuf;
        const char * it = content;
        const char * itE = content + nn;
        for ( ; it != itE; ++it ) {
          if ( *it == '\r' ) {
            *itO++ = '\n';
            if ( it+1 != itE && *(it+1) == '\n' )
              ++it;
          } else {
            *itO++ = *it;
          }
        }
        r.resize( itO-tmpbuf );
        return r;
      };
      expected_text_content = calcExpectedTextCont( content, n );
      ref_content = expected_text_content.c_str();
      ref_n = expected_text_content.size();

      expected_text_content_reducedmaxsize = calcExpectedTextCont( content, reduced_maxsize );

      std::cout<<" --> raw text content: "
               <<fmtText(content,n)<<std::endl;
      std::cout<<" --> expected normalised text content: "
               <<fmtText(expected_text_content)<<std::endl;
      std::cout<<" --> expected normalised text content (reduced maxsize="<<reduced_maxsize<<"): "
               <<fmtText(expected_text_content_reducedmaxsize)<<std::endl;
    }
    writeFile("dummy.bin",content,n);
    std::cout<<"Wrote "<<n<<" bytes"<<std::endl;
    uint64_t read_size;
    char * read_buf;
    mcpl_read_file_to_buffer( "dummy.bin",0,(is_text?1:0),
                              &read_size,&read_buf);
    std::cout<<"Read "<<read_size<<" bytes"<<std::endl;
    if ( is_text )
      std::cout<<" --> actual got normalised text content: "
               <<fmtText(read_buf,read_size)<<std::endl;

    std::cout<<"-->Expected size "<<ref_n<<" and got size "<<read_size<<std::endl;
    if ( read_size != ref_n )
      throw std::runtime_error("Test data read with wrong size");
    if ( 0 != memcmp( read_buf, ref_content, ref_n ) )
      throw std::runtime_error("Test data read wrongly");
    free(read_buf);
    mcpl_read_file_to_buffer( "dummy.bin",reduced_maxsize,(is_text?1:0),
                              &read_size,&read_buf);
    std::cout<<"Read "<<read_size<<" bytes (maxsize="<<reduced_maxsize<<")"<<std::endl;
    if ( is_text )
      std::cout<<" --> actual got normalised text content (with maxsize="
               <<reduced_maxsize<<"): "<<fmtText(read_buf,read_size)<<std::endl;

    if ( is_text ) {
      ref_content = expected_text_content_reducedmaxsize.c_str();
      ref_n = expected_text_content_reducedmaxsize.size();
    } else {
      ref_n = reduced_maxsize;
    }

    if ( read_size != ref_n )
      throw std::runtime_error("Test data read with wrong size (reduced maxsize)");
    if ( 0 != memcmp( read_buf, ref_content, ref_n ) )
      throw std::runtime_error("Test data read wrongly (reduced maxsize)");
    free(read_buf);
    //    free(tmpbuf);
  }
  void testTextData( const char* content, std::size_t n )
  {
    testData(content,n,true);
  }

}


int do_test()
{

  {
    const char data[] = {'a','b','c','d','e',0,'f','g'};
    testData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\r','\n',(char)(unsigned char)(155),'e',0,'\r'};
    testData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\n','\n','a','b','\n'};
    testTextData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\r','b'};
    testTextData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\r','a','b','\n'};
    testTextData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\r','\n','b'};
    testTextData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\r','\n','b','c','\n'};
    testTextData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\r','\n','b','c','\r','\n'};
    testTextData(data,sizeof(data));
  }
  {
    const char data[] = {'\r','\n','a','c','b'};
    testTextData(data,sizeof(data));
  }
  {
    const char data[] = {'a','\r','\n','b','c','\r','\r','\n'};
    testTextData(data,sizeof(data));
  }

  {
    const char data[] = {'a','\r','\n','b','c','\r','\r','\n'};
    testTextData(data,sizeof(data));
  }
  {
    uint64_t rngstate = 0x86A12334;
    auto rng = [&rngstate]() -> uint64_t
    {
      rngstate = (rngstate*1103515245+12345)%2147483648;
      return rngstate;
    };
    auto randint = [&rng](unsigned n)
    {
      return rng() % n;
    };
    for ( unsigned i = 0; i < 1234; ++i )
      rng();
    for ( size_t n : { 7, 1, 0, 65536, 150000 } ) {
      for ( bool is_text : { false, true } ) {
        char * data = (char*)malloc( n ? n : 1 );
        for ( size_t i = 0; i < n; ++i ) {
          char c;
          if ( is_text ) {
            auto j = randint(26);
            if ( j < 4 )
              c = '\r';
            else if ( j < 8 )
              c = '\n';
            else
              c = 'A' + (char)j;
          } else {
            c = (char)randint(256);
          }
          data[i] = c;
        }
        testData(data,n,is_text);
        free(data);
      }
    }
  }

  return 0;
}

int main( int, char** )
{
  int ec(1);
  {
    try {
      std::cout<< "Starting tests"<<std::endl;
      ec = do_test();
      std::cout<< "Tests done"<<std::endl;
    } catch( std::runtime_error& e ) {
      std::cout<< "ERROR: "<<e.what()<<std::endl;
      ec = 1;
    }
  }
  return ec;
}
