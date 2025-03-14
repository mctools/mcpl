
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2025 MCPL developers.                                      ##
##                                                                            ##
##  Licensed under the Apache License, Version 2.0 (the "License");           ##
##  you may not use this file except in compliance with the License.          ##
##  You may obtain a copy of the License at                                   ##
##                                                                            ##
##      http://www.apache.org/licenses/LICENSE-2.0                            ##
##                                                                            ##
##  Unless required by applicable law or agreed to in writing, software       ##
##  distributed under the License is distributed on an "AS IS" BASIS,         ##
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  ##
##  See the License for the specific language governing permissions and       ##
##  limitations under the License.                                            ##
##                                                                            ##
################################################################################

from MCPLTestUtils.dirs import test_data_dir
from MCPLTestUtils.toolcheck_common import ( gunzip, cmd, check_same, copy )
from pathlib import Path
import os
import gzip

def main():
    def dd(fn):
        return test_data_dir.joinpath('ref',fn)
    def ddv2(fn):
        return test_data_dir.joinpath('reffmt2',fn)

    f2 = dd('reffile_16.mcpl')
    f1 = Path('rf16cp.mcpl')
    assert not f1.exists(),"must run in clean directory"
    copy(f2,f1)

    #hard link:
    f1_hl=Path('rf16cp_hl.mcpl')
    os.link(f1,f1_hl)
    assert f1_hl.read_bytes() == f2.read_bytes()
    assert f1_hl.samefile( f1 )
    #soft links:
    f1_sl=Path('rf16cp_sl.mcpl')
    f1_sl.symlink_to(f1)
    f2_sl=Path('rf16_sl.mcpl')
    f2_sl.symlink_to(f2)
    assert f1_sl.read_bytes() == f2.read_bytes()
    assert f2_sl.read_bytes() == f2.read_bytes()
    copy(dd('reffile_5.mcpl'),'rf5cp.mcpl')
    copy(dd('reffile_5.mcpl.gz'),'rf5cp.mcpl.gz')

    fc = copy(dd('reffile_crash.mcpl'),'rfcrash.mcpl')
    fcgz = copy(dd('reffile_crash.mcpl.gz'),'rfcrash.mcpl.gz')

    Path('fake.mcpl').write_bytes(b'lasfsdfsfla\n')
    Path('fake.mcpl.gz').write_bytes(b'lasfsdfsfla\n')
    Path('fake2.mcpl.gz').write_bytes(gzip.compress(b'lasfsdfsfla\n'))

    copy(dd('reffile_empty.mcpl'),'rfempty.mcpl')
    copy(dd('reffile_empty.mcpl.gz'),'rfempty.mcpl.gz')

    fmisc = copy(dd('miscphys.mcpl.gz'),'.')
    fmiscnogz = Path('miscphysnogz.mcpl')
    fmiscnogz.write_bytes(gzip.decompress(fmisc.read_bytes()))

    #file in MCPL-2 format, for testing some commands mixing MCPL-2 and MCPL-3
    #files:
    f2v2 = copy(ddv2('reffile_16.mcpl'),'rf16cp_fmt2.mcpl')
    Path('difficult_unitvector.mcpl').write_bytes(
        gzip.decompress(dd('difficult_unitvector.mcpl.gz').read_bytes())
    )

    #Test various options (also illegal ones):
    cmd('-h')
    cmd('--help')
    cmd('--h')
    cmd('--version')
    cmd('--v')
    cmd(f1,'--justhead')
    cmd(f1,'--ju')
    cmd(f1,'-j')
    cmd(f1,'--nohead')
    cmd(f1,'--n')
    cmd(f1,'--n','-m','--inplace')
    cmd(f1,'--ju','-l2')
    cmd(f1,'--ju','-s1')
    cmd(f1,'-l2','-r')
    cmd(f1,'--v','--h')
    cmd(f1,'--v','--m','--inplace')
    cmd(f1,'-l0','-s2')
    cmd(f1,'-l2','-s0')
    cmd(f1,'-m','--inplace',f2)
    cmd(f1,'-l0')

    #this gives warning on purpose:
    cmd(f1,'--mer','--inpl',f1)
    cmd(f1,'-l0')
    #this gives warning on purpose:
    cmd(f1,'--m','--inplac',f1)
    cmd(f1,'-l0')
    #this gives warning on purpose:
    cmd(f1,'--merge','--inplace',f1)
    #lots of warnings:
    cmd('-m','dupmerge.mcpl',
        f1.name,
        './%s'%f1.name,
        '../%s/%s'%(f1.absolute().parent.name,f1.name),
        f1_sl,
        f1_hl,
        f2_sl,
        f2_sl)
    assert Path('dupmerge.mcpl').is_file()
    cmd('-m','--inplace','dupmerge.mcpl','./dupmerge.mcpl')
    cmd('-m','--inplace','dupmerge.mcpl','dupmerge.mcpl')
    cmd(f1,'-l0')
    cmd('-l0','-s2',dd('reffile_5.mcpl.gz'))
    cmd('-l0','-s2',dd('reffile_5.mcpl'))
    cmd('-l0','-s2',dd('reffile_empty.mcpl'))
    cmd('-l0','-s2',dd('reffile_empty.mcpl.gz'))
    cmd('-m','--inplace','rf5cp.mcpl',dd('reffile_5.mcpl.gz'))
    cmd('-m','--inpla','rf5cp.mcpl.gz',dd('reffile_5.mcpl'))
    cmd('-m','--inplac','rf5cp.mcpl.gz',dd('reffile_5.mcpl.gz'))
    cmd(fc)
    cmd('--repair',fc)
    cmd(fc)
    cmd('--r',fc)
    cmd(fc)
    cmd('-r',fcgz)
    cmd(fc)
    cmd('-r',f1)
    cmd('rfempty.mcpl')
    cmd('-r','rfempty.mcpl')
    cmd('rfempty.mcpl')
    cmd('rfempty.mcpl.gz')
    cmd('-r','rfempty.mcpl.gz')
    cmd('rfempty.mcpl.gz')

    copy(dd('reffile_truncated.mcpl.gz'),'rftrunc.mcpl.gz')
    cmd('-r','rftrunc.mcpl.gz')
    copy(dd('reffile_truncated.mcpl'),'rftrunc.mcpl')
    cmd('-r','rftrunc.mcpl')

    cmd('rftrunc.mcpl')
    cmd('fake.mcpl')
    cmd('fake.mcpl.gz')
    cmd('fake2.mcpl.gz')
    cmd('-e',fmisc,'extracted_1')
    cmd('--extract','-p2112',fmisc,'extracted_1')
    cmd('--extract','-p-11',fmisc,'extracted_2')
    cmd('-ep-1000020040',fmiscnogz,'extracted_3')
    cmd('-e','-p1000922350',fmisc,'extracted_4')
    cmd('-e','-p111','-l999999','-s150',fmiscnogz,'extracted_5')
    cmd('-l0','extracted_1.mcpl.gz')
    cmd('-l0','extracted_2.mcpl.gz')
    cmd('-l0','extracted_3.mcpl.gz')
    cmd('-l0','extracted_4.mcpl.gz')
    cmd('-l0','extracted_5.mcpl.gz')
    #this works because the embedded comment from extracting is (so far) identical:
    cmd('--merge','merged_new_file.mcpl','extracted_1.mcpl.gz','extracted_2.mcpl.gz')
    cmd('--merge','merged_1to5_new_filea.mcpl','extracted_1.mcpl.gz','extracted_2.mcpl.gz','extracted_3.mcpl.gz','extracted_4.mcpl.gz','extracted_5.mcpl.gz')
    gunzip('extracted_1.mcpl.gz')
    gunzip('extracted_2.mcpl.gz')
    cmd('--merge','merged_1to5_new_fileb.mcpl','extracted_1.mcpl','extracted_2.mcpl','extracted_3.mcpl.gz','extracted_4.mcpl.gz','extracted_5.mcpl.gz')
    check_same('merged_1to5_new_filea.mcpl','merged_1to5_new_fileb.mcpl')
    cmd('--merge','--inplace','extracted_1.mcpl','extracted_2.mcpl')
    cmd('extracted_1.mcpl')
    check_same('merged_new_file.mcpl','extracted_1.mcpl')
    check_same('miscphys.mcpl.gz','miscphysnogz.mcpl')
    cmd('--merge','--inplace','extracted_1.mcpl','extracted_3.mcpl.gz','extracted_4.mcpl.gz','extracted_5.mcpl.gz')
    check_same('extracted_1.mcpl','merged_1to5_new_fileb.mcpl')

    gunzip('extracted_3.mcpl.gz')
    gunzip('extracted_4.mcpl.gz')
    gunzip('extracted_5.mcpl.gz')
    cmd('--extract','-p2112',fmiscnogz,'extracted_1_new.mcpl')
    cmd('--extract','-p-11',fmiscnogz,'extracted_2_new.mcpl')
    cmd('-e','-p1000922350',fmiscnogz,'extracted_4_new.mcpl')
    gunzip('extracted_1_new.mcpl.gz')
    gunzip('extracted_2_new.mcpl.gz')
    gunzip('extracted_4_new.mcpl.gz')
    cmd('--merge','merged_1to5_new_filec.mcpl','extracted_1_new.mcpl','extracted_2_new.mcpl','extracted_3.mcpl','extracted_4_new.mcpl','extracted_5.mcpl')
    #merge to gzipped output by specifying .mcpl.gz:
    #  -> but fail since .mcpl file exists:
    cmd('--merge','merged_1to5_new_filec.mcpl.gz','extracted_1_new.mcpl','extracted_2_new.mcpl','extracted_3.mcpl','extracted_4_new.mcpl','extracted_5.mcpl')
    #  -> but fail since wrong ending:
    cmd('--merge','merged_1to5_new_filec.gz','extracted_1_new.mcpl','extracted_2_new.mcpl','extracted_3.mcpl','extracted_4_new.mcpl','extracted_5.mcpl')
    #  -> ok (might fail in old releases if gzip support was absent!):
    cmd('--merge','merged_1to5_new_filec_unique.mcpl.gz','extracted_1_new.mcpl','extracted_2_new.mcpl','extracted_3.mcpl','extracted_4_new.mcpl','extracted_5.mcpl')
    check_same('merged_1to5_new_filec.mcpl','merged_1to5_new_filec_unique.mcpl.gz')

    cmd('--merge','--inplace','extracted_1_new.mcpl','extracted_2_new.mcpl','extracted_3.mcpl','extracted_4_new.mcpl','extracted_5.mcpl')
    check_same('merged_1to5_new_filec.mcpl','extracted_1_new.mcpl')
    check_same('merged_1to5_new_filea.mcpl','merged_1to5_new_filec.mcpl')

    #mistakes with --merge but no --inplace should fail:
    cmd('--merge','extracted_1.mcpl','extracted_2.mcpl')
    #too few pars:
    cmd('--merge','--inplace','extracted_1.mcpl')
    cmd('--merge','newfile.mcpl')
    #error - can't mix MCPL versions when merging inplace:
    cmd('--merge','--inplace',f2v2,f2)
    cmd('--merge','--inplace',f2,f2v2)
    #but ok when not inplace (does trigger warning though):
    cmd('--merge','mix.mcpl',f2v2,f2)
    cmd('-l0','mix.mcpl')
    #test that extraction & merges do not change bytes in transferred particles
    #(using hidden --preventcomment flag):
    cmd('-e','difficult_unitvector.mcpl','extracted_all','-l0','--preventcomment')
    cmd('-e','difficult_unitvector.mcpl','extracted_none','-s999999999','--preventcomment')

    gunzip('extracted_all.mcpl.gz')
    gunzip('extracted_none.mcpl.gz')
    cmd('-m','extracted_recombined','extracted_none.mcpl','extracted_all.mcpl')
    cmd('-m','--inplace','extracted_none.mcpl','extracted_all.mcpl')
    check_same('difficult_unitvector.mcpl','extracted_recombined.mcpl')
    check_same('difficult_unitvector.mcpl','extracted_none.mcpl')
    check_same('extracted_recombined.mcpl','extracted_none.mcpl')
    #More bad files:
    cmd(dd('reffile_bad1.mcpl'))
    cmd(dd('reffile_bad2.mcpl'))
    cmd(dd('reffile_bad3.mcpl'))
    cmd(dd('reffile_bad4.mcpl'))
    cmd(dd('reffile_bad1.mcpl.gz'))
    cmd(dd('reffile_bad2.mcpl.gz'))
    cmd(dd('reffile_bad3.mcpl.gz'))
    cmd(dd('reffile_bad4.mcpl.gz'))
    #missing file (also tests whether or not we complain about the extension):
    cmd('bla.txt')
    Path('bla.txt').write_bytes(b'hello\n')
    #not missing but bad (also tests whether or not we complain about the extension):
    cmd('bla.txt')
    cmd(dd('reffile_truncated.mcpl.gz'))
    cmd(dd('reffile_truncated.mcpl'))
    #This next one opens nicely if mcpltool is build with zlib support, due to the
    #magic of gzopen being able to handle uncompressed files. A bit too magic perhaps...
    cmd(dd('reffile_notreallygz.mcpl.gz'))
    cmd(dd('reffile_uw.mcpl.gz'))

    #This one contains a non-utf8 comment! (fixme: should this actually be forbidden and detected??):
    #print(mcpltool_cmd)
    cmd(dd('reffile_encodings.mcpl.gz'))

    oslash='\u00f8'
    for bk in ['asciidata','asciidata_empty','utf8data','binarydata',f'utf8bl{oslash}bkey']:
        print(f'====> extracting and calculating md5sum of blob with key "{bk}":')
        cmd(dd('reffile_encodings.mcpl.gz'),f'-b{bk}',print_md5sum_of_output=True)

    #FIXME: Not possible apparently to pass b'notutf8key_\xff\xfe_' to subprocess.run:
    #So we are missing the following output:
    #====> extracting and calculating md5sum of blob with key "notutf8key_XXX_":
    #a04637816e7436951f0512d38d48f212

if __name__ == '__main__':
    main()
